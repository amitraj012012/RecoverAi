from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from app.models.recovery_case import RecoveryCase


def get_recovery_case_by_id(db: Session, case_id: str, merchant_id: Optional[str] = None) -> Optional[RecoveryCase]:
    query = db.query(RecoveryCase).options(joinedload(RecoveryCase.payment)).filter(RecoveryCase.id == case_id)
    if merchant_id:
        query = query.filter(RecoveryCase.merchant_id == merchant_id)
    return query.first()


def list_recovery_cases(
    db: Session,
    merchant_id: Optional[str] = None,
    status: Optional[str] = None,
    selected_strategy: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[RecoveryCase], int]:
    query = db.query(RecoveryCase).options(joinedload(RecoveryCase.payment))
    if merchant_id:
        query = query.filter(RecoveryCase.merchant_id == merchant_id)
    if status:
        query = query.filter(RecoveryCase.status == status.upper())
    if selected_strategy:
        query = query.filter(RecoveryCase.selected_strategy == selected_strategy.upper())

    total = query.count()
    items = query.order_by(RecoveryCase.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total
