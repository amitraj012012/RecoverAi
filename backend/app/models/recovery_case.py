from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(64), primary_key=True, index=True)  # e.g. 'rec_...'
    merchant_id = Column(String(64), index=True, nullable=False)
    payment_id = Column(String(64), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    recovery_probability = Column(Float, nullable=True)  # ML prediction
    selected_strategy = Column(String(64), nullable=True)  # Populated in Phase 6
    status = Column(String(32), default="FAILED", nullable=False, index=True)
    # Status values: FAILED, ANALYZING, ACTION_SELECTED, ACTION_EXECUTED, WAITING, VERIFIED, RECOVERED, ESCALATED
    attempt_count = Column(Integer, default=0, nullable=False)
    expected_revenue = Column(Integer, nullable=True)  # in paise
    recovered_amount = Column(Integer, default=0, nullable=False)  # in paise
    simulated_recovery_outcome = Column(Integer, nullable=True)  # 1: recovered, 0: unrecovered (Synthetic Ground Truth)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    payment = relationship("Payment", back_populates="recovery_case")
    actions = relationship("RecoveryAction", back_populates="recovery_case", cascade="all, delete-orphan", order_by="RecoveryAction.executed_at")


Index("idx_recovery_cases_merchant_status", RecoveryCase.merchant_id, RecoveryCase.status)
