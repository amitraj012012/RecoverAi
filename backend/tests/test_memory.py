from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from app.main import app
from app.database.session import SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_memory import RecoveryMemory
from app.models.audit_event import AuditEvent
from app.services.memory_service import (
    record_recovery_experience,
    retrieve_relevant_experiences,
    get_strategy_performance_analytics,
    get_memory_status,
    derive_context_cluster,
    MEMORY_VERSION,
)
from app.services.ai_agent_service import evaluate_recovery_strategy, ALLOWED_STRATEGIES
from app.services.simulator_service import simulate_case_recovery, reset_simulator_state

TEST_SECRET_KEY = "test_super_secret_key_at_least_32_bytes_long_12345"


def get_auth_header(sub="merchant_default", email="merchant@example.com"):
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_memory_recording_and_versioning():
    db = SessionLocal()
    try:
        # Reset case C1024
        case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        if case:
            case.status = "FAILED"
            case.attempt_count = 0
            case.recovered_amount = 0
            db.query(RecoveryMemory).filter(RecoveryMemory.recovery_case_id == "rec_c1024_fail").delete()
            db.commit()

        initial_memories = db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == "merchant_default").count()

        # Simulate execution
        res = simulate_case_recovery(db, "rec_c1024_fail", "merchant_default", scenario="force_success")
        assert res["is_recovered"] is True

        new_memories = db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == "merchant_default").count()
        assert new_memories == initial_memories + 1

        latest_mem = (
            db.query(RecoveryMemory)
            .filter(RecoveryMemory.merchant_id == "merchant_default")
            .order_by(RecoveryMemory.created_at.desc())
            .first()
        )
        assert latest_mem.memory_version == MEMORY_VERSION
        assert latest_mem.is_recovered is True
        assert latest_mem.recovered_amount_paise == 199900
        assert latest_mem.context_cluster is not None
    finally:
        db.close()


def test_memory_retrieval_by_cluster():
    db = SessionLocal()
    try:
        data = retrieve_relevant_experiences(
            db=db,
            merchant_id="merchant_default",
            failure_reason="Card Declined (Insufficient Funds)",
            activity_score=0.88,
            tenure=18,
            limit=5,
        )
        assert "context_cluster" in data
        assert "strategy_performance" in data
        assert data["memory_version"] == MEMORY_VERSION
    finally:
        db.close()


def test_merchant_isolation_memory():
    db = SessionLocal()
    try:
        data_a = retrieve_relevant_experiences(
            db=db,
            merchant_id="merchant_default",
            failure_reason="Card Declined (Insufficient Funds)",
        )
        data_b = retrieve_relevant_experiences(
            db=db,
            merchant_id="merchant_isolated_empty",
            failure_reason="Card Declined (Insufficient Funds)",
        )
        assert data_b["sample_size"] == 0
        assert data_b["strategy_performance"] == {}
    finally:
        db.close()


def test_strategy_performance_aggregation():
    db = SessionLocal()
    try:
        stats = get_strategy_performance_analytics(db, "merchant_default")
        assert isinstance(stats, list)
        if len(stats) > 0:
            assert "strategy" in stats[0]
            assert "recovery_rate" in stats[0]
            assert "recovered_amount_inr" in stats[0]
    finally:
        db.close()


def test_learning_after_failed_outcome():
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        if case:
            case.status = "FAILED"
            case.attempt_count = 0
            case.recovered_amount = 0
            db.commit()

        res = simulate_case_recovery(db, "rec_c1024_fail", "merchant_default", scenario="force_fail")
        assert res["is_recovered"] is False

        latest_mem = (
            db.query(RecoveryMemory)
            .filter(RecoveryMemory.merchant_id == "merchant_default")
            .order_by(RecoveryMemory.created_at.desc())
            .first()
        )
        assert latest_mem.is_recovered is False
        assert latest_mem.recovered_amount_paise == 0
    finally:
        db.close()


def test_memory_api_endpoints():
    with TestClient(app) as client:
        headers = get_auth_header("merchant_default")

        # 1. GET status
        res_stat = client.get("/ai/memory/status", headers=headers)
        assert res_stat.status_code == 200
        assert res_stat.json()["memory_version"] == MEMORY_VERSION

        # 2. GET performance
        res_perf = client.get("/ai/memory/performance", headers=headers)
        assert res_perf.status_code == 200
        assert isinstance(res_perf.json(), list)

        # 3. GET relevant
        res_rel = client.get("/ai/memory/relevant?failure_reason=UPI%20Network%20Timeout", headers=headers)
        assert res_rel.status_code == 200
        assert res_rel.json()["context_cluster"] == "UPI_NETWORK_TIMEOUT"


def test_empirical_memory_override():
    db = SessionLocal()
    merchant_id = "mer_test_adaptive_override"
    try:
        # Cleanup
        db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).delete()
        db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).delete()
        db.query(Payment).filter(Payment.merchant_id == merchant_id).delete()
        db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
        db.commit()

        # Create customer, payment (Card Expired), recovery case
        cust = Customer(
            id="cust_mem_override",
            merchant_id=merchant_id,
            demo_name="Override Test Corp",
            subscription_value=199900,
            tenure=12,
            activity_score=0.85,
        )
        db.add(cust)
        db.flush()

        pay = Payment(
            id="pay_mem_override",
            merchant_id=merchant_id,
            customer_id=cust.id,
            amount=199900,
            currency="INR",
            payment_method="card",
            status="failed",
            failure_reason="Card Expired",
        )
        db.add(pay)
        db.flush()

        case = RecoveryCase(
            id="rec_mem_override",
            merchant_id=merchant_id,
            payment_id=pay.id,
            status="FAILED",
            attempt_count=0,
            expected_revenue=199900,
            recovered_amount=0,
        )
        db.add(case)

        # Baseline check without memory: Card Expired defaults to CREATE_PAYMENT_LINK
        strat_cold, _, _ = evaluate_recovery_strategy(cust, pay, case, ml_probability=0.85, db=db)
        assert strat_cold == "CREATE_PAYMENT_LINK"

        # Now seed 4 successful memories for OFFER_INCENTIVE in the CARD_EXPIRED cluster (100% win-rate)
        for i in range(4):
            mem = RecoveryMemory(
                id=f"mem_test_override_{i}",
                merchant_id=merchant_id,
                recovery_case_id=case.id,
                payment_id=pay.id,
                customer_id=cust.id,
                failure_reason="Card Expired",
                payment_method="card",
                ml_probability=0.85,
                strategy_used="OFFER_INCENTIVE",
                tool_invoked="incentive_offer_simulator",
                outcome_result="SUCCESS",
                is_recovered=True,
                recovered_amount_paise=199900,
                attempt_count=1,
                context_cluster="CARD_EXPIRED",
                memory_version=MEMORY_VERSION,
                created_at=datetime.now(timezone.utc),
            )
            db.add(mem)
        db.commit()

        # Evaluate strategy with memory: OFFER_INCENTIVE should override CREATE_PAYMENT_LINK
        strat_adaptive, reason, conf = evaluate_recovery_strategy(cust, pay, case, ml_probability=0.85, db=db)
        assert strat_adaptive == "OFFER_INCENTIVE"
        assert "Adaptive Memory:" in reason
        assert "OFFER INCENTIVE" in reason
        assert "CARD_EXPIRED" in reason
        assert "100.0%" in reason
        assert conf == 0.95
    finally:
        db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).delete()
        db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).delete()
        db.query(Payment).filter(Payment.merchant_id == merchant_id).delete()
        db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
        db.commit()
        db.close()


def test_max_attempt_guardrail_overriding_memory():
    db = SessionLocal()
    merchant_id = "mer_test_guardrail_override"
    try:
        cust = Customer(id="cust_g1", merchant_id=merchant_id, demo_name="Guardrail Corp", subscription_value=199900, tenure=12, activity_score=0.85)
        pay = Payment(id="pay_g1", merchant_id=merchant_id, customer_id="cust_g1", amount=199900, currency="INR", payment_method="card", status="failed", failure_reason="Card Expired")
        case = RecoveryCase(id="rec_g1", merchant_id=merchant_id, payment_id="pay_g1", status="FAILED", attempt_count=3, expected_revenue=199900)
        db.add_all([cust, pay, case])

        # Seed high-win-rate memory
        for i in range(5):
            mem = RecoveryMemory(
                id=f"mem_g1_{i}", merchant_id=merchant_id, recovery_case_id="rec_g1", payment_id="pay_g1", customer_id="cust_g1",
                failure_reason="Card Expired", payment_method="card", ml_probability=0.90, strategy_used="OFFER_INCENTIVE",
                tool_invoked="incentive_offer_simulator", outcome_result="SUCCESS", is_recovered=True,
                recovered_amount_paise=199900, attempt_count=1, context_cluster="CARD_EXPIRED", memory_version=MEMORY_VERSION,
            )
            db.add(mem)
        db.commit()

        # Guardrail 1 (attempt_count >= 3) MUST override any memory
        strat, reason, conf = evaluate_recovery_strategy(cust, pay, case, ml_probability=0.85, db=db)
        assert strat == "ESCALATE_TO_HUMAN"
        assert "Maximum automatic retry threshold reached" in reason
    finally:
        db.rollback()
        db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).delete()
        db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).delete()
        db.query(Payment).filter(Payment.merchant_id == merchant_id).delete()
        db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
        db.commit()
        db.close()


def test_low_ml_probability_escalation_overriding_memory():
    db = SessionLocal()
    merchant_id = "mer_test_low_ml_override"
    try:
        cust = Customer(id="cust_l1", merchant_id=merchant_id, demo_name="Low ML Corp", subscription_value=199900, tenure=12, activity_score=0.85)
        pay = Payment(id="pay_l1", merchant_id=merchant_id, customer_id="cust_l1", amount=199900, currency="INR", payment_method="card", status="failed", failure_reason="Card Expired")
        case = RecoveryCase(id="rec_l1", merchant_id=merchant_id, payment_id="pay_l1", status="FAILED", attempt_count=0, expected_revenue=199900)
        db.add_all([cust, pay, case])

        # Seed high-win-rate memory
        for i in range(5):
            mem = RecoveryMemory(
                id=f"mem_l1_{i}", merchant_id=merchant_id, recovery_case_id="rec_l1", payment_id="pay_l1", customer_id="cust_l1",
                failure_reason="Card Expired", payment_method="card", ml_probability=0.90, strategy_used="OFFER_INCENTIVE",
                tool_invoked="incentive_offer_simulator", outcome_result="SUCCESS", is_recovered=True,
                recovered_amount_paise=199900, attempt_count=1, context_cluster="CARD_EXPIRED", memory_version=MEMORY_VERSION,
            )
            db.add(mem)
        db.commit()

        # Guardrail 2 (ml_probability < 0.30) MUST override any memory
        strat, reason, conf = evaluate_recovery_strategy(cust, pay, case, ml_probability=0.25, db=db)
        assert strat == "ESCALATE_TO_HUMAN"
        assert "Low recovery probability" in reason
    finally:
        db.rollback()
        db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).delete()
        db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).delete()
        db.query(Payment).filter(Payment.merchant_id == merchant_id).delete()
        db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
        db.commit()
        db.close()


def test_cold_start_heuristic_fallback():
    db = SessionLocal()
    merchant_id = "mer_test_cold_start"
    try:
        cust = Customer(id="cust_c1", merchant_id=merchant_id, demo_name="Cold Start Corp", subscription_value=199900, tenure=6, activity_score=0.50)
        pay = Payment(id="pay_c1", merchant_id=merchant_id, customer_id="cust_c1", amount=199900, currency="INR", payment_method="card", status="failed", failure_reason="Card Expired")
        case = RecoveryCase(id="rec_c1", merchant_id=merchant_id, payment_id="pay_c1", status="FAILED", attempt_count=0, expected_revenue=199900)
        db.add_all([cust, pay, case])
        db.commit()

        # Zero memories -> cold start fallback to deterministic taxonomy
        strat, reason, conf = evaluate_recovery_strategy(cust, pay, case, ml_probability=0.80, db=db)
        assert strat == "CREATE_PAYMENT_LINK"
        assert "Card expired on established customer" in reason
    finally:
        db.rollback()
        db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).delete()
        db.query(Payment).filter(Payment.merchant_id == merchant_id).delete()
        db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
        db.commit()
        db.close()


def test_strategy_allowlist_enforcement_in_memory():
    db = SessionLocal()
    merchant_id = "mer_test_allowlist_memory"
    try:
        cust = Customer(id="cust_a1", merchant_id=merchant_id, demo_name="Allowlist Test Corp", subscription_value=199900, tenure=6, activity_score=0.50)
        pay = Payment(id="pay_a1", merchant_id=merchant_id, customer_id="cust_a1", amount=199900, currency="INR", payment_method="card", status="failed", failure_reason="Card Expired")
        case = RecoveryCase(id="rec_a1", merchant_id=merchant_id, payment_id="pay_a1", status="FAILED", attempt_count=0, expected_revenue=199900)
        db.add_all([cust, pay, case])

        # Seed invalid/unsupported strategy into memory
        for i in range(5):
            mem = RecoveryMemory(
                id=f"mem_inv_{i}", merchant_id=merchant_id, recovery_case_id="rec_a1", payment_id="pay_a1", customer_id="cust_a1",
                failure_reason="Card Expired", payment_method="card", ml_probability=0.90, strategy_used="UNSUPPORTED_HACK_STRATEGY",
                tool_invoked="unknown_tool", outcome_result="SUCCESS", is_recovered=True,
                recovered_amount_paise=199900, attempt_count=1, context_cluster="CARD_EXPIRED", memory_version=MEMORY_VERSION,
            )
            db.add(mem)
        db.commit()

        # Invalid strategy in memory must be rejected; must select allowlisted strategy
        strat, reason, conf = evaluate_recovery_strategy(cust, pay, case, ml_probability=0.80, db=db)
        assert strat in ALLOWED_STRATEGIES
        assert strat == "CREATE_PAYMENT_LINK"
    finally:
        db.rollback()
        db.query(RecoveryMemory).filter(RecoveryMemory.merchant_id == merchant_id).delete()
        db.query(RecoveryCase).filter(RecoveryCase.merchant_id == merchant_id).delete()
        db.query(Payment).filter(Payment.merchant_id == merchant_id).delete()
        db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
        db.commit()
        db.close()

