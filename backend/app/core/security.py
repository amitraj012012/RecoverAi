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

# Supported asymmetric algorithms for Supabase ECC/RSA keys
ASYMMETRIC_ALGORITHMS = ["ES256", "RS256", "EdDSA", "PS256", "ES384", "ES512", "RS384", "RS512"]


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
    Decodes and cryptographically validates a Supabase Auth JWT token:
    1. Asymmetric tokens (ECC P-256 / ES256, RSA / RS256, or tokens with a 'kid' header)
       are verified STRICTLY against the Supabase JWKS endpoint. They NEVER fall back to HMAC.
    2. Symmetric tokens (HMAC / HS256) are verified STRICTLY using SUPABASE_JWT_SECRET.
    
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

    # Branch 1: Asymmetric token verification via JWKS (ES256 / RS256 / kid present)
    is_asymmetric = (alg in ASYMMETRIC_ALGORITHMS) or (kid is not None)

    if is_asymmetric:
        jwks_url = resolve_jwks_url(token)
        try:
            jwks_client = get_jwks_client(jwks_url)
            # Try direct key lookup by kid
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=ASYMMETRIC_ALGORITHMS,
                    options={"verify_aud": False, "verify_exp": True},
                )
                return payload
            except Exception as direct_err:
                # If direct kid matching fails, try all available keys in JWKS set
                jwk_set = jwks_client.get_jwk_set()
                for jwk in jwk_set.keys:
                    try:
                        payload = jwt.decode(
                            token,
                            jwk.key,
                            algorithms=ASYMMETRIC_ALGORITHMS,
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
            logger.warning(f"Asymmetric JWKS JWT verification failed: {str(e)}")
            if is_prod:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token signature.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except Exception as e:
            logger.error(f"Error during JWKS token decoding: {str(e)}")
            if is_prod:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # Branch 2: Symmetric token verification via SUPABASE_JWT_SECRET (HS256 ONLY)
    elif alg == "HS256":
        if is_prod and not settings.SUPABASE_JWT_SECRET:
            logger.error("Production security violation: missing SUPABASE_JWT_SECRET for HS256 token.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Production authentication configuration error: missing SUPABASE_JWT_SECRET for HS256 token.",
            )

        if settings.SUPABASE_JWT_SECRET:
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

    else:
        # Unknown/unsupported algorithm in header
        if is_prod:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported JWT algorithm '{alg}'.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Branch 3: Production Rejection (Strict Security)
    if is_prod:
        logger.warning(f"Production JWT verification failed for token: alg={alg}, kid={kid}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Branch 4: Development / Testing Fallback (for offline test suites and mock tokens)
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
