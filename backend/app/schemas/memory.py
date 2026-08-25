from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MemoryExperienceItem(BaseModel):
    id: str
    recovery_case_id: str
    customer_id: str
    failure_reason: str
    strategy_used: str
    tool_invoked: str
    outcome_result: str
    is_recovered: bool
    recovered_amount_inr: float
    created_at: str


class StrategyWinRateItem(BaseModel):
    attempts: int
    successes: int
    win_rate: float
    win_rate_percentage: float
    total_recovered_paise: int
    total_recovered_inr: float


class RelevantMemoryResponse(BaseModel):
    context_cluster: str
    memory_version: str
    sample_size: int
    strategy_performance: Dict[str, StrategyWinRateItem]
    recent_experiences: List[MemoryExperienceItem]


class StrategyPerformanceResponseItem(BaseModel):
    strategy: str
    label: str
    total_attempts: int
    successful_recoveries: int
    recovery_rate: float
    recovered_amount_paise: int
    recovered_amount_inr: float
    avg_ml_probability: float


class ContextClusterItem(BaseModel):
    cluster: str
    count: int


class MemoryStatusResponse(BaseModel):
    memory_version: str
    total_memory_records: int
    successful_learning_events: int
    last_learned_at: Optional[str]
    context_clusters_tracked: List[ContextClusterItem]
    demo: bool = True
