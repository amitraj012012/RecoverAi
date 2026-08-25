from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(64), primary_key=True, index=True)  # e.g. 'pay_...'
    merchant_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # in paise (e.g. 199900 = ₹1,999)
    currency = Column(String(8), default="INR", nullable=False)
    payment_method = Column(String(32), nullable=False)  # 'card', 'upi', 'netbanking', 'wallet'
    status = Column(String(32), nullable=False, index=True)  # 'success', 'failed', 'pending'
    failure_reason = Column(String(255), nullable=True)  # e.g. 'Card Declined (Insufficient Funds)'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    customer = relationship("Customer", back_populates="payments")
    recovery_case = relationship("RecoveryCase", back_populates="payment", uselist=False, cascade="all, delete-orphan")


Index("idx_payments_merchant_status", Payment.merchant_id, Payment.status)
Index("idx_payments_customer_created", Payment.customer_id, Payment.created_at)
