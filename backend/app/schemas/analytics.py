from typing import List, Optional
from pydantic import BaseModel, Field


class RiskOverviewResponse(BaseModel):
    revenue_at_risk_paise: int = Field(..., description="Total failed payment volume in paise")
    estimated_recoverable_paise: int = Field(..., description="Estimated recoverable revenue in paise (Phase 4 Heuristic)")
    total_volume_paise: int = Field(..., description="Total payment volume in paise")
    success_volume_paise: int = Field(..., description="Successful payment volume in paise")
    total_payment_count: int
    failed_payment_count: int
    success_payment_count: int
    failure_rate: float = Field(..., description="Percentage of failed attempts")
    recovery_case_count: int
    revenue_recovered_paise: Optional[int] = 0


class FailureReasonItem(BaseModel):
    failure_reason: str
    count: int
    revenue_at_risk_paise: int
    percentage_of_risk: float
    percentage_of_failures: float


class PaymentMethodItem(BaseModel):
    payment_method: str
    total_count: int
    total_volume_paise: int
    failed_count: int
    revenue_at_risk_paise: int
    failure_rate: float


class TrendPointItem(BaseModel):
    date: str
    at_risk_paise: int
    success_volume_paise: int
    transaction_count: int
