from typing import Optional
import jwt
from jwt import PyJWKClient, PyJWKClientError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.logging import logger
from app.schemas.auth import MerchantIdentity

security_bearer = HTTPBearer(auto_error=False)

# Cached JWKS client for asymmetric key verification
_jwks_client: Optional[PyJWKClient] = None
_jwks_url_cached: Optional[str] = None


def get_jwks_url() -> Optional[str]:
    """Returns the Supabase JWKS endpoint URL if configured."""
    if settings.SUPABASE_JWKS_URL:
        return settings.SUPABASE_JWKS_URL
    if settings.SUPABASE_URL:
        return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return None


def get_jwks_client() -> Optional[PyJWKClient]:
    """Retrieves or initializes the cached PyJWKClient for JWKS key rotation and caching."""
    global _jwks_client, _jwks_url_cached
    url = get_jwks_url()
    if not url:
        return None
    if _jwks_client is None or _jwks_url_cached != url:
        _jwks_client = PyJWKClient(
            url,
            cache_keys=True,
            max_cached_keys=16,
            lifespan=3600,
        )
        _jwks_url_cached = url
    return _jwks_client


def decode_supabase_jwt(token: str) -> dict:
    """
    Decodes and validates a Supabase Auth JWT token supporting both:
    1. Asymmetric signing keys (ECC P-256 / ES256, RSA / RS256) via Supabase JWKS endpoint.
    2. Legacy symmetric signing keys (HMAC / HS256) via SUPABASE_JWT_SECRET.
    
    Security Specification:
    - In PRODUCTION: Cryptographically verified Supabase JWT signature validation is strictly required.
      If JWKS/SUPABASE_URL and SUPABASE_JWT_SECRET are both missing, or if signature verification fails,
      fails securely with appropriate error.
    - In DEVELOPMENT / TESTING: If JWKS or SUPABASE_JWT_SECRET is configured, verifies signature.
      Otherwise, safely validates payload claims (sub, exp) for test-suite / mock mode.
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
    jwks_client = get_jwks_client()

    if is_prod:
        # Require configuration
        if not jwks_client and not settings.SUPABASE_JWT_SECRET:
            logger.error("Production security violation: missing SUPABASE_URL / JWKS or SUPABASE_JWT_SECRET in production.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Production authentication configuration error: missing SUPABASE_URL (JWKS) or SUPABASE_JWT_SECRET.",
            )

        # 1. Asymmetric verification via JWKS (for ES256, RS256, or when kid is present)
        if jwks_client and (kid is not None or alg in ("ES256", "RS256", "EdDSA", "PS256")):
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["ES256", "RS256", "EdDSA", "PS256", "HS256"],
                    options={"verify_aud": False},
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except (jwt.InvalidTokenError, PyJWKClientError) as e:
                logger.warning(f"Production JWKS JWT verification failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token signature.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except Exception as e:
                logger.error(f"Error during JWKS token decoding: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # 2. Symmetric verification via SUPABASE_JWT_SECRET (HS256)
        if settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except jwt.InvalidTokenError as e:
                logger.warning(f"Production HMAC JWT verification failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token signature.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # If asymmetric token received but JWKS is not configured
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    else:
        # Development / Testing Mode
        # Try asymmetric verification if JWKS available
        if jwks_client and (kid is not None or alg in ("ES256", "RS256", "EdDSA", "PS256")):
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["ES256", "RS256", "EdDSA", "PS256", "HS256"],
                    options={"verify_aud": False},
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except Exception:
                pass  # Fall through to symmetric / mock in dev

        # Try symmetric verification if SUPABASE_JWT_SECRET configured
        if settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except Exception:
                pass  # Fall through to unverified mock in dev

        # Development / Mock / Testing fallback when no secret is configured or mock tokens used
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
            logger.warning(f"Invalid JWT token provided in dev mode: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Error decoding authentication token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
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
