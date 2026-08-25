from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class RecoveryExecutionResponse(BaseModel):
    recovery_case_id: str
    payment_id: str
    customer_id: str
    amount_paise: int
    amount_inr: float
    ml_probability: float
    ml_probability_percentage: float
    selected_strategy: str
    decision_reason: str
    confidence: float
    tool_invoked: str
    tool_result: str
    recovery_action_id: str
    current_status: str
    attempt_count: int
    recovered_amount_paise: int
    is_recovered: bool
    demo: bool = True


class AiDecisionLogItem(BaseModel):
    id: str
    recovery_case_id: str
    event_type: str
    actor: str
    metadata: Dict[str, Any]
    created_at: datetime


class RecoveryCaseWorkflowResponse(BaseModel):
    case_id: str
    payment_id: str
    customer_id: str
    amount_inr: float
    failure_reason: Optional[str]
    status: str
    ml_probability: Optional[float]
    selected_strategy: Optional[str]
    attempt_count: int
    recovered_amount_inr: float
    actions: List[Dict[str, Any]]
    audit_events: List[Dict[str, Any]]
