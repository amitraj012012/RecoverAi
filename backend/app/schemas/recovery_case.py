from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RecoveryCaseBase(BaseModel):
    payment_id: str
    recovery_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    selected_strategy: Optional[str] = None
    status: str = "FAILED"
    attempt_count: int = 0
    expected_revenue: Optional[int] = None
    recovered_amount: int = 0


class RecoveryCaseCreate(RecoveryCaseBase):
    id: str
    merchant_id: str


class RecoveryCaseResponse(RecoveryCaseBase):
    id: str
    merchant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecoveryCaseListResponse(BaseModel):
    items: List[RecoveryCaseResponse]
    total: int
    page: int
    limit: int
