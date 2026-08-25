from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.schemas.memory import (
    MemoryStatusResponse,
    RelevantMemoryResponse,
    StrategyPerformanceResponseItem,
)
from app.services.memory_service import (
    get_memory_status,
    retrieve_relevant_experiences,
    get_strategy_performance_analytics,
)

router = APIRouter(prefix="/ai/memory", tags=["Adaptive Agent Memory & Continuous Learning"])


@router.get("/status", response_model=MemoryStatusResponse)
async def get_memory_status_endpoint(
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns adaptive memory status, total learning records, and tracked context clusters.
    """
    try:
        return get_memory_status(db=db, merchant_id=merchant.merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching memory status: {str(e)}")


@router.get("/performance", response_model=List[StrategyPerformanceResponseItem])
async def get_strategy_performance_endpoint(
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Aggregates empirical strategy performance from actual simulator outcome memories.
    """
    try:
        return get_strategy_performance_analytics(db=db, merchant_id=merchant.merchant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching strategy performance: {str(e)}")


@router.get("/relevant", response_model=RelevantMemoryResponse)
async def get_relevant_memory_endpoint(
    failure_reason: str = Query("Card Declined (Insufficient Funds)"),
    activity_score: float = Query(0.5),
    tenure: int = Query(6),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Retrieves bounded relevant historical recovery experiences matching the given context cluster.
    """
    try:
        return retrieve_relevant_experiences(
            db=db,
            merchant_id=merchant.merchant_id,
            failure_reason=failure_reason,
            activity_score=activity_score,
            tenure=tenure,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memory: {str(e)}")
