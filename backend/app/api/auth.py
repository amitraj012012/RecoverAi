from fastapi import APIRouter, Depends
from app.core.security import get_current_merchant
from app.schemas.auth import AuthMessageResponse, MerchantIdentity

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=MerchantIdentity)
async def get_current_merchant_profile(
    current_merchant: MerchantIdentity = Depends(get_current_merchant),
) -> MerchantIdentity:
    """
    Returns the authenticated merchant identity extracted securely from the Bearer token.
    """
    return current_merchant


@router.post("/logout", response_model=AuthMessageResponse)
async def logout_merchant(
    current_merchant: MerchantIdentity = Depends(get_current_merchant),
) -> AuthMessageResponse:
    """
    Acknowledges merchant session termination.
    """
    return AuthMessageResponse(
        message=f"Merchant session for {current_merchant.email} terminated successfully.",
        success=True,
    )
