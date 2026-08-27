from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.logging import logger
from app.schemas.auth import MerchantIdentity

security_bearer = HTTPBearer(auto_error=False)


def decode_supabase_jwt(token: str) -> dict:
    """
    Decodes and validates a Supabase Auth JWT token.
    
    Security Specification:
    - In PRODUCTION: Cryptographically verified Supabase JWT validation is strictly required.
      If SUPABASE_JWT_SECRET is missing or the signature is invalid, fails securely.
    - In DEVELOPMENT / TESTING: If SUPABASE_JWT_SECRET is configured, verifies signature.
      Otherwise, safely validates payload claims (sub, exp) for test-suite / mock mode.
    """
    is_prod = settings.ENVIRONMENT.lower() in ("production", "prod")

    if is_prod:
        if not settings.SUPABASE_JWT_SECRET:
            logger.error("Production security violation: SUPABASE_JWT_SECRET is missing in production environment.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Production authentication configuration error: missing SUPABASE_JWT_SECRET.",
            )
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
            logger.warning(f"Production JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token signature.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # Development / Testing Mode
        try:
            if settings.SUPABASE_JWT_SECRET:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
            else:
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
            logger.warning(f"Invalid JWT token provided: {str(e)}")
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
