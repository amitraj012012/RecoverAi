from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RecoveryActionBase(BaseModel):
    recovery_case_id: str
    action_type: str
    agent_reason: Optional[str] = None
    result: str = "PENDING"
    metadata_json: Optional[str] = None


class RecoveryActionCreate(RecoveryActionBase):
    id: str


class RecoveryActionResponse(RecoveryActionBase):
    id: str
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
