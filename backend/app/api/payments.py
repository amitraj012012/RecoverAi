from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.schemas.payment import (
    PaymentEventIngest,
    PaymentResponse,
    PaymentListResponse,
)
from app.services.payment_service import (
    get_payment_by_id,
    list_payments,
    ingest_payment_event,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/events", response_model=PaymentResponse, status_code=201)
async def ingest_payment(
    event: PaymentEventIngest,
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Ingests a payment event. If status is 'failed', creates an initial recovery case.
    """
    payment, _ = ingest_payment_event(db, event, default_merchant_id=merchant.merchant_id)
    return payment


@router.get("", response_model=PaymentListResponse)
async def get_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns paginated payment transactions for the authenticated merchant workspace.
    """
    items, total = list_payments(
        db,
        merchant_id=merchant.merchant_id,
        customer_id=customer_id,
        status=status,
        payment_method=payment_method,
        page=page,
        limit=limit,
    )
    return PaymentListResponse(
        items=[PaymentResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns a specific payment transaction by ID.
    """
    payment = get_payment_by_id(db, payment_id=payment_id, merchant_id=merchant.merchant_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found")
    return payment
