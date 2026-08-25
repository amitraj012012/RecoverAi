from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.schemas.payment import PaymentCreate, PaymentEventIngest


def get_payment_by_id(db: Session, payment_id: str, merchant_id: Optional[str] = None) -> Optional[Payment]:
    query = db.query(Payment).filter(Payment.id == payment_id)
    if merchant_id:
        query = query.filter(Payment.merchant_id == merchant_id)
    return query.first()


def list_payments(
    db: Session,
    merchant_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[Payment], int]:
    query = db.query(Payment)
    if merchant_id:
        query = query.filter(Payment.merchant_id == merchant_id)
    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)
    if status:
        query = query.filter(Payment.status == status.lower())
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method.lower())

    total = query.count()
    items = query.order_by(Payment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total


def ingest_payment_event(db: Session, event: PaymentEventIngest, default_merchant_id: str) -> Tuple[Payment, Optional[RecoveryCase]]:
    merchant_id = event.merchant_id or default_merchant_id

    # Check if payment already exists
    existing = db.query(Payment).filter(Payment.id == event.id).first()
    if existing:
        return existing, existing.recovery_case

    db_payment = Payment(
        id=event.id,
        merchant_id=merchant_id,
        customer_id=event.customer_id,
        amount=event.amount,
        currency=event.currency,
        payment_method=event.payment_method,
        status=event.status.lower(),
        failure_reason=event.failure_reason,
    )
    db.add(db_payment)
    db.flush()

    recovery_case = None
    # If payment failed, create initial recovery case
    if db_payment.status == "failed":
        recovery_case = RecoveryCase(
            id=f"rec_{db_payment.id.replace('pay_', '')}",
            merchant_id=merchant_id,
            payment_id=db_payment.id,
            status="FAILED",
            attempt_count=0,
            expected_revenue=db_payment.amount,
            recovered_amount=0,
        )
        db.add(recovery_case)

    db.commit()
    db.refresh(db_payment)
    if recovery_case:
        db.refresh(recovery_case)

    return db_payment, recovery_case
