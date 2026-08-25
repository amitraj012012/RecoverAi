from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, ConfigDict


class CustomerBase(BaseModel):
    demo_name: str
    subscription_value: int = Field(..., description="Subscription value in paise (e.g. 199900 = ₹1,999)")
    tenure: int = Field(1, description="Customer tenure in months")
    activity_score: float = Field(0.5, ge=0.0, le=1.0, description="Activity score from 0.0 to 1.0")


class CustomerCreate(CustomerBase):
    id: str
    merchant_id: str


class CustomerResponse(CustomerBase):
    id: str
    merchant_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    limit: int
