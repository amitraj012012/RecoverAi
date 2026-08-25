from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_current_merchant
from app.schemas.auth import MerchantIdentity
from app.schemas.customer import CustomerResponse, CustomerListResponse
from app.services.customer_service import get_customer_by_id, list_customers

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=CustomerListResponse)
async def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns paginated customers for the authenticated merchant workspace.
    """
    items, total = list_customers(
        db,
        merchant_id=merchant.merchant_id,
        search=search,
        page=page,
        limit=limit,
    )
    return CustomerListResponse(
        items=[CustomerResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    merchant: MerchantIdentity = Depends(get_current_merchant),
):
    """
    Returns a customer profile by ID.
    """
    customer = get_customer_by_id(db, customer_id=customer_id, merchant_id=merchant.merchant_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
