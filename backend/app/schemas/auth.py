from typing import Optional
from pydantic import BaseModel, EmailStr


class MerchantIdentity(BaseModel):
    merchant_id: str
    email: EmailStr
    role: Optional[str] = "authenticated"


class AuthMessageResponse(BaseModel):
    message: str
    success: bool
