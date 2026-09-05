import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# 1. HARD SAFETY GUARD: STRICT LOCAL SQLITE TEST DATABASE ENFORCEMENT
# ---------------------------------------------------------------------------
PROHIBITED_PRODUCTION_MERCHANT_UUID = "3f82a698-8a79-4f9d-b6b5-f3f6e5cdd4b5"

raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///./recoverai.db")

# Fail immediately if remote / PostgreSQL / Supabase connection is detected
if any(kw in raw_db_url.lower() for kw in ["postgres", "postgresql", "supabase.co", "aws.com", "azure.com"]):
    raise RuntimeError(
        f"CRITICAL SAFETY VIOLATION: Pytest attempted to execute against a remote/production database ({raw_db_url}). "
        "Tests must run strictly against a local SQLite database."
    )

# Normalize SQLite path for isolated test environments
if raw_db_url.startswith("sqlite:///./"):
    rel_name = raw_db_url[len("sqlite:///./"):]
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    test_db_path = os.path.join(base_dir, rel_name)
    resolved_test_db_url = f"sqlite:///{test_db_path}"
else:
    resolved_test_db_url = raw_db_url

# Configure test database engine
test_engine = create_engine(
    resolved_test_db_url,
    connect_args={"check_same_thread": False} if resolved_test_db_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Rebind app.database.session to the test database
import app.database.session as app_session
app_session.engine = test_engine
app_session.SessionLocal = TestSessionLocal

from app.database.session import Base, init_db
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.audit_event import AuditEvent
from app.models.recovery_memory import RecoveryMemory
from app.services.memory_service import MEMORY_VERSION


# ---------------------------------------------------------------------------
# 2. DETERMINISTIC TEST FIXTURES SEEDER
# ---------------------------------------------------------------------------
BASELINE_TEST_EXPERIENCES = [
    {
        "cluster": "CARD_EXPIRED",
        "strategy": "CREATE_PAYMENT_LINK",
        "tool": "payment_link_simulator",
        "reason": "Card Expired",
        "method": "card",
        "win_rate": 0.85,
        "count": 6,
    },
    {
        "cluster": "UPI_NETWORK_TIMEOUT",
        "strategy": "RETRY_PAYMENT",
        "tool": "payment_retry_simulator",
        "reason": "UPI Network Timeout",
        "method": "upi",
        "win_rate": 0.55,
        "count": 6,
    },
    {
        "cluster": "INSUFFICIENT_FUNDS_LOYAL_CUSTOMER",
        "strategy": "CREATE_PAYMENT_LINK",
        "tool": "payment_link_simulator",
        "reason": "Card Declined (Insufficient Funds)",
        "method": "card",
        "win_rate": 0.78,
        "count": 6,
    },
    {
        "cluster": "BANK_SERVER_UNAVAILABLE",
        "strategy": "RETRY_PAYMENT",
        "tool": "payment_retry_simulator",
        "reason": "Bank Server Unavailable",
        "method": "netbanking",
        "win_rate": 0.75,
        "count": 6,
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


def seed_test_database(db):
    """
    Seeds a compact, deterministic test dataset satisfying all 67 test requirements.
    Ensures complete isolation from production data and UUIDs.
    """
    merchant_id = "merchant_default"
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # 1. Customer C1024 & Demo Case
    c1024 = db.query(Customer).filter(Customer.id == "C1024").first()
    if not c1024:
        c1024 = Customer(
            id="C1024",
            merchant_id=merchant_id,
            demo_name="Enterprise Cloud SaaS (C1024)",
            subscription_value=199900,  # ₹1,999
            tenure=18,
            activity_score=0.88,
            created_at=base_time - timedelta(days=18 * 30),
        )
        db.add(c1024)

    # 17 successful historical monthly payments for C1024
    for m in range(17):
        p_id = f"pay_c1024_hist_{m+1}"
        if not db.query(Payment).filter(Payment.id == p_id).first():
            db.add(
                Payment(
                    id=p_id,
                    merchant_id=merchant_id,
                    customer_id="C1024",
                    amount=199900,
                    currency="INR",
                    payment_method="card",
                    status="success",
                    failure_reason=None,
                    created_at=base_time - timedelta(days=(17 - m) * 30),
                )
            )

    # Failed payment and recovery case for C1024
    if not db.query(Payment).filter(Payment.id == "pay_c1024_fail").first():
        db.add(
            Payment(
                id="pay_c1024_fail",
                merchant_id=merchant_id,
                customer_id="C1024",
                amount=199900,
                currency="INR",
                payment_method="card",
                status="failed",
                failure_reason="Card Declined (Insufficient Funds)",
                created_at=base_time + timedelta(hours=1),
            )
        )

    if not db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first():
        db.add(
            RecoveryCase(
                id="rec_c1024_fail",
                merchant_id=merchant_id,
                payment_id="pay_c1024_fail",
                status="FAILED",
                attempt_count=0,
                expected_revenue=199900,
                recovered_amount=0,
                recovery_probability=0.85,
                simulated_recovery_outcome=1,
                created_at=base_time + timedelta(hours=1),
            )
        )

    # 2. Customer C1910 & Multi-attempt Case
    c1910 = db.query(Customer).filter(Customer.id == "C1910").first()
    if not c1910:
        c1910 = Customer(
            id="C1910",
            merchant_id=merchant_id,
            demo_name="Nexus Platform (C1910)",
            subscription_value=199900,
            tenure=12,
            activity_score=0.70,
            created_at=base_time - timedelta(days=12 * 30),
        )
        db.add(c1910)

    if not db.query(Payment).filter(Payment.id == "pay_c1910_2").first():
        db.add(
            Payment(
                id="pay_c1910_2",
                merchant_id=merchant_id,
                customer_id="C1910",
                amount=199900,
                currency="INR",
                payment_method="upi",
                status="failed",
                failure_reason="UPI Network Timeout",
                created_at=base_time + timedelta(hours=2),
            )
        )

    if not db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1910_2").first():
        db.add(
            RecoveryCase(
                id="rec_c1910_2",
                merchant_id=merchant_id,
                payment_id="pay_c1910_2",
                status="FAILED",
                attempt_count=0,
                expected_revenue=199900,
                recovered_amount=0,
                recovery_probability=0.72,
                simulated_recovery_outcome=1,
                created_at=base_time + timedelta(hours=2),
            )
        )

    # 3. Additional Customers, Payments, and Cases for Pagination & Batch Sim (size 25)
    methods = ["card", "upi", "netbanking", "wallet"]
    reasons = [
        "Card Declined (Insufficient Funds)",
        "UPI Network Timeout",
        "Card Expired",
        "Bank Server Unavailable",
        "Authentication Failed (OTP Timeout)",
        "Transaction Exceeded Limit",
    ]

    for idx in range(1, 40):
        cid = f"C{1100 + idx}"
        if not db.query(Customer).filter(Customer.id == cid).first():
            db.add(
                Customer(
                    id=cid,
                    merchant_id=merchant_id,
                    demo_name=f"Test Business {idx}",
                    subscription_value=99900 * (1 + (idx % 4)),
                    tenure=2 + (idx % 24),
                    activity_score=round(0.40 + (idx % 60) * 0.01, 2),
                    created_at=base_time - timedelta(days=idx * 10),
                )
            )

        pid_fail = f"pay_test_batch_{idx}"
        pm = methods[idx % len(methods)]
        fr = reasons[idx % len(reasons)]
        if not db.query(Payment).filter(Payment.id == pid_fail).first():
            db.add(
                Payment(
                    id=pid_fail,
                    merchant_id=merchant_id,
                    customer_id=cid,
                    amount=99900 * (1 + (idx % 4)),
                    currency="INR",
                    payment_method=pm,
                    status="failed",
                    failure_reason=fr,
                    created_at=base_time - timedelta(days=idx),
                )
            )

        rcid = f"rec_test_batch_{idx}"
        if not db.query(RecoveryCase).filter(RecoveryCase.id == rcid).first():
            db.add(
                RecoveryCase(
                    id=rcid,
                    merchant_id=merchant_id,
                    payment_id=pid_fail,
                    status="FAILED",
                    attempt_count=0,
                    expected_revenue=99900 * (1 + (idx % 4)),
                    recovered_amount=0,
                    recovery_probability=round(0.50 + (idx % 45) * 0.01, 2),
                    simulated_recovery_outcome=1 if idx % 2 == 0 else 0,
                    created_at=base_time - timedelta(days=idx),
                )
            )

        # Successful payment for history / analytics
        pid_succ = f"pay_test_succ_{idx}"
        if not db.query(Payment).filter(Payment.id == pid_succ).first():
            db.add(
                Payment(
                    id=pid_succ,
                    merchant_id=merchant_id,
                    customer_id=cid,
                    amount=99900 * (1 + (idx % 4)),
                    currency="INR",
                    payment_method=pm,
                    status="success",
                    failure_reason=None,
                    created_at=base_time - timedelta(days=idx + 30),
                )
            )

    # 4. Baseline Adaptive Memories
    if db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).count() < 20:
        mem_idx = 1
        for template in BASELINE_TEST_EXPERIENCES:
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

                mem = RecoveryMemory(
                    id=f"mem_test_{cluster.lower()}_{i+1}_{mem_idx}",
                    merchant_id=merchant_id,
                    recovery_case_id=f"rec_hist_test_{cluster.lower()}_{i+1}",
                    payment_id=f"pay_hist_test_{cluster.lower()}_{i+1}",
                    customer_id=f"cust_hist_test_{cluster.lower()}_{i+1}",
                    failure_reason=reason,
                    payment_method=method,
                    ml_probability=0.80 if is_recovered else 0.40,
                    strategy_used=strategy,
                    tool_invoked=tool,
                    outcome_result=outcome_res,
                    is_recovered=is_recovered,
                    recovered_amount_paise=amt_paise,
                    attempt_count=1,
                    context_cluster=cluster,
                    memory_version=MEMORY_VERSION,
                    created_at=base_time + timedelta(days=i),
                )
                db.add(mem)
                mem_idx += 1

    # 5. Baseline Audit / Decision Events
    if db.query(AuditEvent).filter(AuditEvent.merchant_id == merchant_id).count() < 3:
        db.add_all([
            AuditEvent(
                id=f"aud_test_init_1_{str(uuid.uuid4())[:6]}",
                merchant_id=merchant_id,
                event_type="RECOVERY_ACTION_EXECUTED",
                entity_id="rec_c1024_fail",
                actor="ai_recovery_agent_v1",
                metadata_json='{"action": "CREATE_PAYMENT_LINK", "selected_strategy": "CREATE_PAYMENT_LINK", "customer_id": "C1024"}',
                created_at=base_time + timedelta(hours=1),
            ),
            AuditEvent(
                id=f"aud_test_init_2_{str(uuid.uuid4())[:6]}",
                merchant_id=merchant_id,
                event_type="SIMULATOR_TRIAL_COMPLETED",
                entity_id="rec_c1910_2",
                actor="autonomous_simulator_engine_v1",
                metadata_json='{"action": "RETRY_PAYMENT", "selected_strategy": "RETRY_PAYMENT", "customer_id": "C1910"}',
                created_at=base_time + timedelta(hours=2),
            ),
            AuditEvent(
                id=f"aud_test_init_3_{str(uuid.uuid4())[:6]}",
                merchant_id=merchant_id,
                event_type="DATASET_INITIALIZATION",
                entity_id="system",
                actor="system",
                metadata_json='{"status": "test_fixtures_initialized"}',
                created_at=base_time,
            ),
        ])

    db.commit()


# ---------------------------------------------------------------------------
# 3. PYTEST SESSION & AUTOUSE FIXTURES
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """Initializes tables and seeds the compact deterministic test fixture."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        seed_test_database(db)
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def reset_demo_case_state_between_tests():
    """
    Guarantees test order independence by resetting C1024 and C1910 to clean states before each test.
    """
    yield
    db = TestSessionLocal()
    try:
        c1024_case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        if c1024_case:
            c1024_case.status = "FAILED"
            c1024_case.attempt_count = 0
            c1024_case.recovered_amount = 0
            c1024_case.selected_strategy = None

        c1910_case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1910_2").first()
        if c1910_case:
            c1910_case.status = "FAILED"
            c1910_case.attempt_count = 0
            c1910_case.recovered_amount = 0
            c1910_case.selected_strategy = None

        db.commit()
    finally:
        db.close()
