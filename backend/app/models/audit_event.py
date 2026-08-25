from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from app.database.session import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), index=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    actor = Column(String(64), default="system", nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
