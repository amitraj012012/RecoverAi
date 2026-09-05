from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)  # e.g. 'C1024'
    merchant_id = Column(String(64), primary_key=True, index=True, nullable=False)
    demo_name = Column(String(255), nullable=False)
    subscription_value = Column(Integer, nullable=False, default=0)  # in paise
    tenure = Column(Integer, nullable=False, default=1)  # in months
    activity_score = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    payments = relationship(
        "Payment",
        primaryjoin="and_(Customer.id==Payment.customer_id, Customer.merchant_id==Payment.merchant_id)",
        foreign_keys="[Payment.customer_id, Payment.merchant_id]",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
