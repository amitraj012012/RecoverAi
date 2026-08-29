import re
from typing import Optional, Dict
import jwt
from jwt import PyJWKClient, PyJWKClientError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.logging import logger
from app.schemas.auth import MerchantIdentity

security_bearer = HTTPBearer(auto_error=False)

# Cached JWKS clients keyed by JWKS URL
_jwks_clients: Dict[str, PyJWKClient] = {}

# Default project JWKS URL fallback
DEFAULT_SUPABASE_JWKS_URL = "https://omeaqucqnmlfvwmuvdel.supabase.co/auth/v1/.well-known/jwks.json"


def resolve_jwks_url(unverified_token: Optional[str] = None) -> str:
    """
    Resolves the Supabase JWKS endpoint URL from multiple configuration and token hints:
    1. Explicit SUPABASE_JWKS_URL setting.
    2. SUPABASE_URL setting.
    3. Token 'iss' (issuer) claim if from a Supabase project.
    4. DATABASE_URL if it contains a Supabase host (db.<ref>.supabase.co).
    5. Default project JWKS fallback.
    """
    if settings.SUPABASE_JWKS_URL:
        return settings.SUPABASE_JWKS_URL

    if settings.SUPABASE_URL:
        base = settings.SUPABASE_URL.rstrip("/")
        if base.endswith("/auth/v1"):
            return f"{base}/.well-known/jwks.json"
        return f"{base}/auth/v1/.well-known/jwks.json"

    # Check token issuer claim
    if unverified_token:
        try:
            unverified_payload = jwt.decode(unverified_token, options={"verify_signature": False})
            iss = unverified_payload.get("iss", "")
            if "supabase.co" in iss:
                base_iss = iss.rstrip("/")
                if base_iss.endswith("/auth/v1"):
                    return f"{base_iss}/.well-known/jwks.json"
                return f"{base_iss}/auth/v1/.well-known/jwks.json"
        except Exception:
            pass

    # Check DATABASE_URL for Supabase project ref
    if settings.DATABASE_URL:
        match = re.search(r"db\.([a-z0-9]+)\.supabase\.co", settings.DATABASE_URL)
        if match:
            project_ref = match.group(1)
            return f"https://{project_ref}.supabase.co/auth/v1/.well-known/jwks.json"

    return DEFAULT_SUPABASE_JWKS_URL


def get_jwks_client(jwks_url: str) -> PyJWKClient:
    """Retrieves or initializes a cached PyJWKClient for a specific JWKS endpoint."""
    global _jwks_clients
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(
            jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            lifespan=3600,
        )
    return _jwks_clients[jwks_url]


def decode_supabase_jwt(token: str) -> dict:
    """
    Decodes and cryptographically validates a Supabase Auth JWT token supporting:
    1. Asymmetric signing keys (ECC P-256 / ES256, RSA / RS256) via Supabase JWKS endpoint.
    2. Symmetric signing keys (HMAC / HS256) via SUPABASE_JWT_SECRET.
    
    Security Specification:
    - In PRODUCTION: Cryptographically verified signature validation is strictly enforced.
    - In DEVELOPMENT / TESTING: Verifies signature if keys are available, with safe mock fallback.
    """
    is_prod = settings.ENVIRONMENT.lower() in ("production", "prod")

    # Extract unverified token header to inspect alg and kid
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as e:
        logger.warning(f"Failed to parse JWT header: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    alg = unverified_header.get("alg", "HS256")
    kid = unverified_header.get("kid")
    jwks_url = resolve_jwks_url(token)
    jwks_client = get_jwks_client(jwks_url) if jwks_url else None

    allowed_algorithms = ["ES256", "RS256", "EdDSA", "PS256", "HS256", "ES384", "ES512", "RS384", "RS512"]

    # 1. Asymmetric verification via JWKS (for ES256, RS256, or when kid / JWKS is present)
    if jwks_client and (kid is not None or alg in ("ES256", "RS256", "EdDSA", "PS256", "ES384", "ES512")):
        try:
            # First try matching by kid
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=allowed_algorithms,
                    options={"verify_aud": False, "verify_exp": True},
                )
                return payload
            except Exception as direct_err:
                # If kid matching failed, try all available JWKS keys
                jwk_set = jwks_client.get_jwk_set()
                for jwk in jwk_set.keys:
                    try:
                        payload = jwt.decode(
                            token,
                            jwk.key,
                            algorithms=allowed_algorithms,
                            options={"verify_aud": False, "verify_exp": True},
                        )
                        return payload
                    except jwt.InvalidTokenError:
                        continue
                raise direct_err

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.InvalidTokenError, PyJWKClientError) as e:
            logger.warning(f"JWKS signature verification failed: {str(e)}")
            if is_prod:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token signature.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # 2. Symmetric verification via SUPABASE_JWT_SECRET (HS256)
    if settings.SUPABASE_JWT_SECRET and alg == "HS256":
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False, "verify_exp": True},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"HMAC JWT verification failed: {str(e)}")
            if is_prod:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token signature.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # In Production, reject if neither JWKS nor HMAC signature passed
    if is_prod:
        logger.warning(f"Production JWT verification failed: alg={alg}, kid={kid}, jwks_url={jwks_url}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Development / Testing Fallback (for offline test suites and mock tokens)
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token in dev mode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_merchant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> MerchantIdentity:
    """
    FastAPI dependency to extract and verify the authenticated merchant identity from request.
    Rejects any unauthenticated or tampered requests with 401 Unauthorized.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_supabase_jwt(token)

    merchant_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", "authenticated")

    if not merchant_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing merchant identification.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return MerchantIdentity(
        merchant_id=str(merchant_id),
        email=str(email),
        role=str(role),
    )
