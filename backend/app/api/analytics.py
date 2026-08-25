from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.schemas.analytics import (
    RiskOverviewResponse,
    FailureReasonItem,
    PaymentMethodItem,
    TrendPointItem,
)
from app.services.risk_engine_service import (
    calculate_merchant_risk_overview,
    get_failure_reasons_breakdown,
    get_payment_methods_breakdown,
    get_revenue_trends,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & Risk Engine"])


@router.get("/overview", response_model=RiskOverviewResponse)
async def get_analytics_overview(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns merchant-scoped revenue risk, estimated recoverable revenue, and failure metrics.
    """
    return calculate_merchant_risk_overview(
        db,
        merchant_id=merchant.merchant_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/failure-reasons", response_model=List[FailureReasonItem])
async def get_failure_reasons(
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns breakdown of failed transactions grouped by failure reason.
    """
    return get_failure_reasons_breakdown(db, merchant_id=merchant.merchant_id)


@router.get("/payment-methods", response_model=List[PaymentMethodItem])
async def get_payment_methods(
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns breakdown of transaction volume and failure rates by payment method.
    """
    return get_payment_methods_breakdown(db, merchant_id=merchant.merchant_id)


@router.get("/trends", response_model=List[TrendPointItem])
async def get_trends(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    limit: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns time-series revenue at risk and transaction volume from actual database timestamps.
    """
    return get_revenue_trends(
        db,
        merchant_id=merchant.merchant_id,
        period=period,
        limit=limit,
    )
