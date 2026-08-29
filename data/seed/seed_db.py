import os
import sys
import argparse
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

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
from app.models.recovery_action import RecoveryAction
from app.models.audit_event import AuditEvent
from app.models.recovery_memory import RecoveryMemory
from data.generators.synthetic_data import generate_synthetic_dataset
from app.services.ml_prediction_service import populate_all_recovery_probabilities
from app.services.memory_service import derive_context_cluster, MEMORY_VERSION


# Baseline historical memory experiences template
BASELINE_CLUSTER_EXPERIENCES = [
    {
        "cluster": "CARD_EXPIRED",
        "strategy": "CREATE_PAYMENT_LINK",
        "tool": "payment_link_simulator",
        "reason": "Card Expired",
        "method": "card",
        "win_rate": 0.85,
        "count": 12,
    },
    {
        "cluster": "UPI_NETWORK_TIMEOUT",
        "strategy": "RETRY_PAYMENT",
        "tool": "payment_retry_simulator",
        "reason": "UPI Network Timeout",
        "method": "upi",
        "win_rate": 0.82,
        "count": 10,
    },
    {
        "cluster": "INSUFFICIENT_FUNDS_LOYAL_CUSTOMER",
        "strategy": "CREATE_PAYMENT_LINK",
        "tool": "payment_link_simulator",
        "reason": "Card Declined (Insufficient Funds)",
        "method": "card",
        "win_rate": 0.78,
        "count": 10,
    },
    {
        "cluster": "BANK_SERVER_UNAVAILABLE",
        "strategy": "RETRY_PAYMENT",
        "tool": "payment_retry_simulator",
        "reason": "Bank Server Unavailable",
        "method": "netbanking",
        "win_rate": 0.75,
        "count": 8,
    },
    {
        "cluster": "INSUFFICIENT_FUNDS_CHURN_RISK",
        "strategy": "OFFER_INCENTIVE",
        "tool": "incentive_offer_simulator",
        "reason": "Card Declined (Insufficient Funds)",
        "method": "card",
        "win_rate": 0.60,
        "count": 6,
    },
    {
        "cluster": "TRANSACTION_LIMIT_EXCEEDED",
        "strategy": "ALTERNATE_PAYMENT_METHOD",
        "tool": "payment_method_update_simulator",
        "reason": "Transaction Exceeded Limit",
        "method": "upi",
        "win_rate": 0.55,
        "count": 6,
    },
]


def seed_adaptive_memories(db, merchant_id: str):
    """
    Seeds baseline historical recovery memory experiences across clusters for the merchant.
    Ensures empirical win-rates and adaptive retrieval are populated immediately.
    """
    existing_mem_count = db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).count()
    if existing_mem_count >= 30:
        print(f"  - Adaptive memories already present ({existing_mem_count} records). Skipping memory seed.")
        return

    print("  - Seeding baseline historical recovery memories across context clusters...")
    memories = []
    base_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    mem_idx = 1
    for template in BASELINE_CLUSTER_EXPERIENCES:
        cluster = template["cluster"]
        strategy = template["strategy"]
        tool = template["tool"]
        reason = template["reason"]
        method = template["method"]
        win_rate = template["win_rate"]
        count = template["count"]

        for i in range(count):
            is_recovered = (i / count) < win_rate
            outcome_res = "SUCCESS" if is_recovered else "FAILED"
            amt_paise = 199900 if is_recovered else 0
            created_dt = base_time + timedelta(days=i * 2, hours=i * 3)

            mem_id = f"mem_seed_{cluster.lower()}_{i+1}_{str(uuid.uuid4())[:6]}"
            mem = RecoveryMemory(
                id=mem_id,
                merchant_id=merchant_id,
                recovery_case_id=f"rec_hist_{cluster.lower()}_{i+1}",
                payment_id=f"pay_hist_{cluster.lower()}_{i+1}",
                customer_id=f"cust_hist_{cluster.lower()}_{i+1}",
                failure_reason=reason,
                payment_method=method,
                ml_probability=round(0.70 + (0.20 if is_recovered else -0.20), 2),
                strategy_used=strategy,
                tool_invoked=tool,
                outcome_result=outcome_res,
                is_recovered=is_recovered,
                recovered_amount_paise=amt_paise,
                attempt_count=1,
                context_cluster=cluster,
                memory_version=MEMORY_VERSION,
                created_at=created_dt,
            )
            memories.append(mem)
            mem_idx += 1

    db.bulk_save_objects(memories)
    db.commit()
    print(f"  - Inserted {len(memories)} baseline adaptive memory records.")


def seed_baseline_audit_events(db, merchant_id: str):
    """
    Seeds initial system audit events for activity feed.
    """
    existing_events = db.query(AuditEvent).filter(AuditEvent.merchant_id == merchant_id).count()
    if existing_events >= 5:
        return

    print("  - Seeding initial audit events...")
    events = [
        AuditEvent(
            id=f"evt_init_1_{str(uuid.uuid4())[:6]}",
            merchant_id=merchant_id,
            event_type="DATASET_INITIALIZATION",
            entity_id="system",
            actor="system",
            metadata_json='{"action": "seeded_synthetic_dataset", "records": 21648}',
            created_at=datetime.now(timezone.utc) - timedelta(hours=24),
        ),
        AuditEvent(
            id=f"evt_init_2_{str(uuid.uuid4())[:6]}",
            merchant_id=merchant_id,
            event_type="ML_RISK_ENGINE_ACTIVATED",
            entity_id="logistic-regression-v2",
            actor="ml_engine",
            metadata_json='{"model": "logistic-regression-v2", "status": "active"}',
            created_at=datetime.now(timezone.utc) - timedelta(hours=18),
        ),
        AuditEvent(
            id=f"evt_init_3_{str(uuid.uuid4())[:6]}",
            merchant_id=merchant_id,
            event_type="ADAPTIVE_MEMORY_SYNC",
            entity_id="agent-memory-v1",
            actor="memory_engine",
            metadata_json='{"clusters_indexed": 6, "status": "synced"}',
            created_at=datetime.now(timezone.utc) - timedelta(hours=12),
        ),
    ]
    db.bulk_save_objects(events)
    db.commit()


def seed_database(
    merchant_id: str = "merchant_default",
    target_payments: int = 10000,
    clean: bool = False,
    drop_tables: bool = False,
    recalculate_ml: bool = True,
    seed_memory: bool = True,
):
    """
    Idempotent seeding function compatible with Supabase PostgreSQL and local SQLite.
    """
    print("==================================================================")
    print(" RecoverAI — Synthetic Database Seeder")
    print(f" Target Merchant ID: {merchant_id}")
    print(f" Database URL Target: {engine.url.render_as_string(hide_password=True)}")
    print(f" Clean Reseed: {clean} | Drop Tables: {drop_tables}")
    print("==================================================================")

    if drop_tables:
        print("Dropping all existing database tables...")
        Base.metadata.drop_all(bind=engine)

    # Initialize tables if not existing
    init_db()
    db = SessionLocal()

    try:
        if clean:
            print(f"Cleaning existing records for merchant '{merchant_id}'...")
            db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).delete()
            db.query(RecoveryAction).filter(
                RecoveryAction.recovery_case_id.in_(
                    db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == merchant_id)
                )
            ).delete(synchronize_session=False)
            db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).delete()
            db.query(Payment).filter(Payment.merchant_id == merchant_id).delete()
            db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
            db.query(AuditEvent).filter(AuditEvent.merchant_id == merchant_id).delete()
            db.commit()

        # Check existing data for idempotency
        existing_customers = db.query(Customer).filter(Customer.merchant_id == merchant_id).count()
        if existing_customers > 0 and not clean:
            print(f"Found {existing_customers} existing customer records for merchant '{merchant_id}'.")
            print("Skipping raw customer/payment re-insertion (idempotent mode).")
        else:
            print(f"Generating synthetic dataset (1,200 customers, target min {target_payments} payments)...")
            dataset = generate_synthetic_dataset(
                num_customers=1200,
                target_min_payments=target_payments,
                merchant_id=merchant_id,
                seed=42,
            )

            print(f"Inserting {len(dataset['customers'])} customer records...")
            db_customers = [
                Customer(
                    id=c["id"],
                    merchant_id=c["merchant_id"],
                    demo_name=c["demo_name"],
                    subscription_value=c["subscription_value"],
                    tenure=c["tenure"],
                    activity_score=c["activity_score"],
                    created_at=datetime.fromisoformat(c["created_at"]),
                )
                for c in dataset["customers"]
            ]
            db.bulk_save_objects(db_customers)
            db.commit()

            print(f"Inserting {len(dataset['payments'])} payment records in batches...")
            batch_size = 2000
            db_payments = []
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

        # Step 2: Calculate & Populate ML Recovery Probabilities
        if recalculate_ml:
            print("Calculating ML recovery probabilities via logistic-regression-v2...")
            unscored = db.query(RecoveryCase).filter(
                RecoveryCase.merchant_id == merchant_id,
                RecoveryCase.recovery_probability.is_(None),
            ).count()
            if unscored > 0 or clean:
                updated_count = populate_all_recovery_probabilities(db, merchant_id=merchant_id)
                print(f"  - Populated ML recovery probability for {updated_count} cases.")
            else:
                print("  - All recovery cases already have ML probabilities calculated.")

        # Step 3: Seed Adaptive Memories
        if seed_memory:
            seed_adaptive_memories(db, merchant_id=merchant_id)
            seed_baseline_audit_events(db, merchant_id=merchant_id)

        # Final Verification
        final_customers = db.query(Customer).filter(Customer.merchant_id == merchant_id).count()
        final_payments = db.query(Payment).filter(Payment.merchant_id == merchant_id).count()
        success_payments = db.query(Payment).filter(Payment.merchant_id == merchant_id, Payment.status == "success").count()
        failed_payments = db.query(Payment).filter(Payment.merchant_id == merchant_id, Payment.status == "failed").count()
        final_cases = db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).count()
        final_memories = db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).count()
        final_events = db.query(AuditEvent).filter(AuditEvent.merchant_id == merchant_id).count()

        c1024_case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        c1024_prob = f"{c1024_case.recovery_probability * 100:.1f}%" if c1024_case and c1024_case.recovery_probability else "N/A"

        print("==================================================================")
        print(" Seeding Completed Successfully! Summary:")
        print(f"  - Merchant ID: {merchant_id}")
        print(f"  - Total Customers: {final_customers}")
        print(f"  - Total Payments: {final_payments} ({success_payments} success, {failed_payments} failed)")
        print(f"  - Total Recovery Cases: {final_cases}")
        print(f"  - Demo Case C1024 Score: {c1024_prob}")
        print(f"  - Total Adaptive Memories: {final_memories}")
        print(f"  - Total Audit Events: {final_events}")
        print("==================================================================")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RecoverAI Database Seeder")
    parser.add_argument("--merchant-id", default=os.getenv("SEED_MERCHANT_ID", "merchant_default"), help="Merchant ID to seed")
    parser.add_argument("--clean", action="store_true", help="Clean existing merchant records before reseed")
    parser.add_argument("--drop-all", action="store_true", help="Drop all tables and recreate (destructive)")
    parser.add_argument("--target-payments", type=int, default=10000, help="Target minimum payment count")
    args = parser.parse_args()

    seed_database(
        merchant_id=args.merchant_id,
        target_payments=args.target_payments,
        clean=args.clean,
        drop_tables=args.drop_all,
    )
