from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.schemas.recovery_case import RecoveryCaseResponse, RecoveryCaseListResponse
from app.services.recovery_case_service import get_recovery_case_by_id, list_recovery_cases

router = APIRouter(prefix="/recovery-cases", tags=["Recovery Cases"])


@router.get("", response_model=RecoveryCaseListResponse)
async def get_recovery_cases(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    selected_strategy: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns paginated recovery cases for the authenticated merchant.
    """
    items, total = list_recovery_cases(
        db,
        merchant_id=merchant.merchant_id,
        status=status,
        selected_strategy=selected_strategy,
        page=page,
        limit=limit,
    )
    return RecoveryCaseListResponse(
        items=[RecoveryCaseResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{case_id}", response_model=RecoveryCaseResponse)
async def get_recovery_case(
    case_id: str,
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns a specific recovery case by ID.
    """
    case = get_recovery_case_by_id(db, case_id=case_id, merchant_id=merchant.merchant_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    return case
