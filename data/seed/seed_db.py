import os
import sys
from datetime import datetime

# Add root directory and backend directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
backend_dir = os.path.join(root_dir, "backend")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.session import SessionLocal, init_db, engine, Base
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from data.generators.synthetic_data import generate_synthetic_dataset


def seed_database(merchant_id: str = "merchant_default", target_payments: int = 10000, clean: bool = True):
    print(f"Initializing database (clean={clean}) and seeding synthetic payment records...")
    
    if clean:
        print("Dropping existing tables for clean canonical reseed...")
        Base.metadata.drop_all(bind=engine)
    
    init_db()
    db = SessionLocal()

    try:
        # If not clean reseed, check if merchant data already exists
        if not clean:
            existing_count = db.query(Customer).filter(Customer.merchant_id == merchant_id).count()
            if existing_count > 0:
                print(f"Database already contains {existing_count} records for merchant '{merchant_id}'. Skipping duplicate seeding.")
                return

        dataset = generate_synthetic_dataset(
            num_customers=1200,
            target_min_payments=target_payments,
            merchant_id=merchant_id,
            seed=42,
        )

        print(f"Inserting {len(dataset['customers'])} customer records...")
        db_customers = []
        for c in dataset["customers"]:
            db_customers.append(
                Customer(
                    id=c["id"],
                    merchant_id=c["merchant_id"],
                    demo_name=c["demo_name"],
                    subscription_value=c["subscription_value"],
                    tenure=c["tenure"],
                    activity_score=c["activity_score"],
                    created_at=datetime.fromisoformat(c["created_at"]),
                )
            )
        db.bulk_save_objects(db_customers)
        db.commit()

        print(f"Inserting {len(dataset['payments'])} payment records in batches...")
        db_payments = []
        batch_size = 2000
        for p in dataset["payments"]:
            db_payments.append(
                Payment(
                    id=p["id"],
                    merchant_id=p["merchant_id"],
                    customer_id=p["customer_id"],
                    amount=p["amount"],
                    currency=p["currency"],
                    payment_method=p["payment_method"],
                    status=p["status"],
                    failure_reason=p["failure_reason"],
                    created_at=datetime.fromisoformat(p["created_at"]),
                )
            )
            if len(db_payments) >= batch_size:
                db.bulk_save_objects(db_payments)
                db.commit()
                db_payments = []

        if db_payments:
            db.bulk_save_objects(db_payments)
            db.commit()

        print(f"Inserting {len(dataset['recovery_cases'])} recovery cases...")
        db_cases = []
        for rc in dataset["recovery_cases"]:
            db_cases.append(
                RecoveryCase(
                    id=rc["id"],
                    merchant_id=rc["merchant_id"],
                    payment_id=rc["payment_id"],
                    status=rc["status"],
                    attempt_count=rc["attempt_count"],
                    expected_revenue=rc["expected_revenue"],
                    recovered_amount=rc["recovered_amount"],
                    simulated_recovery_outcome=rc.get("simulated_recovery_outcome"),
                    created_at=datetime.fromisoformat(rc["created_at"]),
                )
            )
            if len(db_cases) >= batch_size:
                db.bulk_save_objects(db_cases)
                db.commit()
                db_cases = []

        if db_cases:
            db.bulk_save_objects(db_cases)
            db.commit()

        final_payments = db.query(Payment).count()
        success_payments = db.query(Payment).filter(Payment.status == "success").count()
        failed_payments = db.query(Payment).filter(Payment.status == "failed").count()
        final_customers = db.query(Customer).count()
        final_cases = db.query(RecoveryCase).count()
        pos_outcomes = db.query(RecoveryCase).filter(RecoveryCase.simulated_recovery_outcome == 1).count()
        neg_outcomes = db.query(RecoveryCase).filter(RecoveryCase.simulated_recovery_outcome == 0).count()

        print("Seeding completed successfully! Canonical database state:")
        print(f"  - Total Customers: {final_customers}")
        print(f"  - Total Payments: {final_payments} ({success_payments} successful, {failed_payments} failed)")
        print(f"  - Total Recovery Cases: {final_cases}")
        print(f"  - Simulated Recovery Outcomes: {pos_outcomes} Recovered, {neg_outcomes} Unrecovered")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(clean=True)
