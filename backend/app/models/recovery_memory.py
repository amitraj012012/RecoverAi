from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Index
from app.database.session import Base


class RecoveryMemory(Base):
    __tablename__ = "recovery_memories"

    id = Column(String(64), primary_key=True, index=True)  # e.g. 'mem_...'
    merchant_id = Column(String(64), index=True, nullable=False)
    recovery_case_id = Column(String(64), index=True, nullable=False)
    payment_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=False)
    failure_reason = Column(String(128), nullable=False, index=True)
    payment_method = Column(String(32), nullable=False)
    ml_probability = Column(Float, nullable=False)
    strategy_used = Column(String(64), nullable=False, index=True)
    tool_invoked = Column(String(64), nullable=False)
    outcome_result = Column(String(32), nullable=False)  # SUCCESS, FAILED, ESCALATED, PENDING_CUSTOMER_ACTION
    is_recovered = Column(Boolean, default=False, nullable=False)
    recovered_amount_paise = Column(Integer, default=0, nullable=False)
    attempt_count = Column(Integer, default=1, nullable=False)
    context_cluster = Column(String(64), nullable=False, index=True)
    memory_version = Column(String(32), default="agent-memory-v1", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


Index("idx_recovery_memories_merchant_context", RecoveryMemory.merchant_id, RecoveryMemory.context_cluster)
Index("idx_recovery_memories_merchant_strategy", RecoveryMemory.merchant_id, RecoveryMemory.strategy_used)
