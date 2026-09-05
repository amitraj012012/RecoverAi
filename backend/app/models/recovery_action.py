from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String(64), primary_key=True, index=True)  # e.g. 'act_...'
    recovery_case_id = Column(String(64), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)
    # Allowed: RETRY_PAYMENT, CREATE_PAYMENT_LINK, ALTERNATE_PAYMENT_METHOD, SEND_REMINDER, OFFER_INCENTIVE, ESCALATE_TO_HUMAN
    agent_reason = Column(Text, nullable=True)
    result = Column(String(32), default="PENDING", nullable=False)  # SUCCESS, FAILED, PENDING
    metadata_json = Column(Text, nullable=True)  # JSON-encoded metadata
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    recovery_case = relationship(
        "RecoveryCase",
        primaryjoin="RecoveryAction.recovery_case_id==RecoveryCase.id",
        foreign_keys=[recovery_case_id],
        back_populates="actions",
    )
