from typing import List, Optional
from pydantic import BaseModel, Field


class PredictRecoveryRequest(BaseModel):
    payment_id: Optional[str] = None
    recovery_case_id: Optional[str] = None


class FactorItem(BaseModel):
    feature: str
    impact: str  # positive, negative, neutral
    description: str


class PredictRecoveryResponse(BaseModel):
    payment_id: str
    recovery_case_id: Optional[str] = None
    customer_id: str
    recovery_probability: float = Field(..., ge=0.0, le=1.0)
    recovery_probability_percentage: float
    model_version: str
    factors: List[FactorItem]
