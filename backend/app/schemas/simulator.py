from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class CaseSimulationRequest(BaseModel):
    scenario: str = Field("auto", description="Simulation scenario: 'auto', 'force_success', 'force_fail', 'force_escalate'")


class BatchSimulationRequest(BaseModel):
    batch_size: int = Field(25, ge=1, le=200, description="Number of active cases to simulate")
    scenario: str = Field("auto", description="Simulation scenario: 'auto', 'force_success', 'force_fail'")


class CaseSimulationResponse(BaseModel):
    recovery_case_id: str
    payment_id: str
    customer_id: str
    original_amount_paise: int
    original_amount_inr: float
    recovered_amount_paise: int
    recovered_amount_inr: float
    ml_probability: float
    ml_probability_percentage: float
    selected_strategy: str
    decision_reason: str
    tool_invoked: str
    tool_result: str
    recovery_action_id: str
    current_status: str
    attempt_count: int
    is_recovered: bool
    scenario: str
    demo: bool = True


class BatchSimulationResponse(BaseModel):
    batch_size_requested: int
    cases_processed: int
    recovered_count: int
    escalated_count: int
    still_active_count: int
    total_recovered_paise: int
    total_recovered_inr: float
    simulation_results: List[CaseSimulationResponse]
    demo: bool = True


class SimulatorMetricsResponse(BaseModel):
    total_recovery_cases: int
    failed_cases: int
    in_progress_cases: int
    recovered_cases: int
    escalated_cases: int
    recovery_rate_percentage: float
    total_revenue_recovered_paise: int
    total_revenue_recovered_inr: float
    revenue_still_at_risk_paise: int
    revenue_still_at_risk_inr: float
    demo: bool = True


class SimulatorResetResponse(BaseModel):
    reset_status: str
    cases_reset: int
    message: str
    demo: bool = True
