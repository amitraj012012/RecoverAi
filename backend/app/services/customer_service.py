from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


def get_customer_by_id(db: Session, customer_id: str, merchant_id: Optional[str] = None) -> Optional[Customer]:
    query = db.query(Customer).filter(Customer.id == customer_id)
    if merchant_id:
        query = query.filter(Customer.merchant_id == merchant_id)
    return query.first()


def list_customers(
    db: Session,
    merchant_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Tuple[List[Customer], int]:
    query = db.query(Customer)
    if merchant_id:
        query = query.filter(Customer.merchant_id == merchant_id)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Customer.demo_name.ilike(search_pattern)) | (Customer.id.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(Customer.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total


def create_customer(db: Session, customer_in: CustomerCreate) -> Customer:
    existing = db.query(Customer).filter(Customer.id == customer_in.id).first()
    if existing:
        return existing

    db_customer = Customer(
        id=customer_in.id,
        merchant_id=customer_in.merchant_id,
        demo_name=customer_in.demo_name,
        subscription_value=customer_in.subscription_value,
        tenure=customer_in.tenure,
        activity_score=customer_in.activity_score,
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer
