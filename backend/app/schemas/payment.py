from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PaymentBase(BaseModel):
    customer_id: str
    amount: int = Field(..., description="Amount in paise (e.g. 199900 = ₹1,999)")
    currency: str = "INR"
    payment_method: str = Field(..., description="Method: card, upi, netbanking, wallet")
    status: str = Field(..., description="Status: success, failed, pending")
    failure_reason: Optional[str] = None


class PaymentCreate(PaymentBase):
    id: str
    merchant_id: str
    created_at: Optional[datetime] = None


class PaymentEventIngest(PaymentBase):
    id: str
    merchant_id: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: str
    merchant_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    limit: int
