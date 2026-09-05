from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from app.main import app
from app.database.session import SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.audit_event import AuditEvent
from app.services.simulator_service import (
    simulate_case_recovery,
    run_batch_simulation,
    get_simulator_metrics,
    reset_simulator_state,
)

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


def test_single_case_simulation_auto():
    db = SessionLocal()
    try:
        # Reset C1024 to FAILED
        case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        if case:
            case.status = "FAILED"
            case.attempt_count = 0
            case.recovered_amount = 0
            db.commit()

        res = simulate_case_recovery(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default", scenario="auto")
        assert res["recovery_case_id"] == "rec_c1024_fail"
        assert res["customer_id"] == "C1024"
        assert res["original_amount_paise"] == 199900
        assert res["current_status"] in ["RECOVERED", "ACTION_EXECUTED", "ESCALATED"]
        assert res["demo"] is True
    finally:
        db.close()


def test_single_case_simulation_forced_success():
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        if case:
            case.status = "FAILED"
            case.attempt_count = 0
            case.recovered_amount = 0
            db.commit()

        res = simulate_case_recovery(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default", scenario="force_success")
        assert res["current_status"] == "RECOVERED"
        assert res["is_recovered"] is True
        assert res["recovered_amount_paise"] == 199900
        assert res["recovered_amount_inr"] == 1999.0
    finally:
        db.close()


def test_single_case_simulation_forced_failure():
    db = SessionLocal()
    try:
        # Reset C1024 to FAILED for clean failure test
        case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        if case:
            case.status = "FAILED"
            case.attempt_count = 0
            case.recovered_amount = 0
            db.commit()

        res = simulate_case_recovery(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default", scenario="force_fail")
        assert res["current_status"] == "ACTION_EXECUTED"
        assert res["is_recovered"] is False
        assert res["recovered_amount_paise"] == 0
    finally:
        db.close()


def test_single_case_simulation_forced_escalate():
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).filter(RecoveryCase.status.in_(["FAILED", "ACTION_EXECUTED"])).first()
        if case:
            res = simulate_case_recovery(db, recovery_case_id=case.id, merchant_id="merchant_default", scenario="force_escalate")
            assert res["current_status"] == "ESCALATED"
            assert res["selected_strategy"] == "ESCALATE_TO_HUMAN"
    finally:
        db.close()


def test_batch_simulation_runner():
    db = SessionLocal()
    try:
        # Ensure batch test cases are in FAILED state for runner
        db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == "merchant_default",
            RecoveryCase.id.like("rec_test_batch_%"),
        ).update({"status": "FAILED", "recovered_amount": 0, "attempt_count": 0, "selected_strategy": None}, synchronize_session=False)
        db.commit()

        for size in [10, 25]:
            res = run_batch_simulation(db, merchant_id="merchant_default", batch_size=size, scenario="auto")
            assert res["cases_processed"] > 0
            assert res["total_recovered_paise"] >= 0
            assert "simulation_results" in res
            assert len(res["simulation_results"]) == res["cases_processed"]
    finally:
        db.close()


def test_simulator_status_metrics():
    db = SessionLocal()
    try:
        metrics = get_simulator_metrics(db, merchant_id="merchant_default")
        assert metrics["total_recovery_cases"] > 0
        assert metrics["demo"] is True
        assert metrics["total_revenue_recovered_paise"] >= 0
        assert metrics["revenue_still_at_risk_paise"] >= 0
    finally:
        db.close()


def test_c1024_consecutive_preset_switching():
    db = SessionLocal()
    try:
        # Run 1: Force Success
        res1 = simulate_case_recovery(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default", scenario="force_success")
        assert res1["current_status"] == "RECOVERED"
        assert res1["is_recovered"] is True

        # Run 2: Immediately Force Fail on the already-recovered C1024 demo case
        res2 = simulate_case_recovery(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default", scenario="force_fail")
        assert res2["current_status"] == "ACTION_EXECUTED"
        assert res2["is_recovered"] is False

        # Run 3: Immediately Force Escalate
        res3 = simulate_case_recovery(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default", scenario="force_escalate")
        assert res3["current_status"] == "ESCALATED"
        assert res3["selected_strategy"] == "ESCALATE_TO_HUMAN"

        # Run 4: Immediately Auto (Stochastic ML)
        res4 = simulate_case_recovery(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default", scenario="auto")
        assert res4["customer_id"] == "C1024"
        assert res4["original_amount_paise"] == 199900
    finally:
        db.close()


def test_duplicate_simulation_prevention():
    db = SessionLocal()
    test_merchant_id = "merchant_test_terminal_sim"
    try:
        # Create dedicated isolated test entities
        cust = Customer(
            id="C_TEST_TERM_SIM",
            merchant_id=test_merchant_id,
            demo_name="Terminal Sim Test Corp",
            subscription_value=199900,
            tenure=12,
            activity_score=0.80,
        )
        pay = Payment(
            id="pay_test_term_sim",
            merchant_id=test_merchant_id,
            customer_id="C_TEST_TERM_SIM",
            amount=199900,
            currency="INR",
            payment_method="card",
            status="failed",
            failure_reason="Card Expired",
        )
        case = RecoveryCase(
            id="rec_test_term_sim",
            merchant_id=test_merchant_id,
            payment_id="pay_test_term_sim",
            status="RECOVERED",
            attempt_count=1,
            expected_revenue=199900,
            recovered_amount=199900,
        )
        db.add_all([cust, pay, case])
        db.commit()

        # Verify terminal recovery cases cannot be simulated again
        with pytest.raises(ValueError, match="already in terminal state"):
            simulate_case_recovery(db, recovery_case_id="rec_test_term_sim", merchant_id=test_merchant_id)
    finally:
        db.query(RecoveryAction).filter(
            RecoveryAction.recovery_case_id.in_(
                db.query(RecoveryCase.id).filter(RecoveryCase.merchant_id == test_merchant_id)
            )
        ).delete(synchronize_session=False)
        db.query(RecoveryCase).filter(RecoveryCase.merchant_id == test_merchant_id).delete()
        db.query(Payment).filter(Payment.merchant_id == test_merchant_id).delete()
        db.query(Customer).filter(Customer.merchant_id == test_merchant_id).delete()
        db.commit()
        db.close()


def test_api_simulator_endpoints():
    with TestClient(app) as client:
        headers = get_auth_header()

        # 1. GET status
        res_stat = client.get("/simulator/status", headers=headers)
        assert res_stat.status_code == 200
        assert res_stat.json()["demo"] is True

        # 2. POST run batch
        res_run = client.post("/simulator/run", json={"batch_size": 5, "scenario": "auto"}, headers=headers)
        assert res_run.status_code == 200
        assert "cases_processed" in res_run.json()

        # 3. POST single case
        db = SessionLocal()
        case = db.query(RecoveryCase).filter(RecoveryCase.status == "FAILED").first()
        case_id = case.id if case else "rec_c1024_fail"
        db.close()

        res_case = client.post(f"/simulator/case/{case_id}", json={"scenario": "auto"}, headers=headers)
        assert res_case.status_code in [200, 400]


def test_merchant_isolation_simulator():
    with TestClient(app) as client:
        headers_b = get_auth_header(sub="merchant_other_unauthorized", email="other@test.com")
        res = client.post("/simulator/case/rec_c1024_fail", json={"scenario": "auto"}, headers=headers_b)
        assert res.status_code == 400
        assert "not found or unauthorized" in res.json()["detail"].lower()


def test_calculate_effective_recovery_probability_all_strategies():
    from app.services.tool_registry import calculate_effective_recovery_probability, STRATEGY_EFFICACY

    # 1. Verify exact calibration coefficients at attempt 0
    assert STRATEGY_EFFICACY["RETRY_PAYMENT"] == 0.70
    assert STRATEGY_EFFICACY["CREATE_PAYMENT_LINK"] == 0.55
    assert STRATEGY_EFFICACY["ALTERNATE_PAYMENT_METHOD"] == 0.45
    assert STRATEGY_EFFICACY["OFFER_INCENTIVE"] == 0.40
    assert STRATEGY_EFFICACY["SEND_REMINDER"] == 0.35

    # 2. Verify Peff calculation with ML prob = 0.80
    assert round(calculate_effective_recovery_probability(0.80, "RETRY_PAYMENT", 0), 4) == 0.56
    assert round(calculate_effective_recovery_probability(0.80, "CREATE_PAYMENT_LINK", 0), 4) == 0.44
    assert round(calculate_effective_recovery_probability(0.80, "ALTERNATE_PAYMENT_METHOD", 0), 4) == 0.36
    assert round(calculate_effective_recovery_probability(0.80, "OFFER_INCENTIVE", 0), 4) == 0.32
    assert round(calculate_effective_recovery_probability(0.80, "SEND_REMINDER", 0), 4) == 0.28


def test_attempt_decay_and_clamping():
    from app.services.tool_registry import calculate_effective_recovery_probability

    ml_p = 0.90
    strat = "RETRY_PAYMENT"  # efficacy = 0.70 -> base Peff = 0.63

    # Attempt 0: factor = 1.00
    p0 = calculate_effective_recovery_probability(ml_p, strat, 0)
    assert round(p0, 4) == 0.63

    # Attempt 1: factor = 0.85
    p1 = calculate_effective_recovery_probability(ml_p, strat, 1)
    assert round(p1, 4) == round(0.63 * 0.85, 4)  # 0.5355

    # Attempt 2: factor = 0.7225
    p2 = calculate_effective_recovery_probability(ml_p, strat, 2)
    assert round(p2, 4) == round(0.63 * 0.7225, 4)  # 0.4552

    # Clamping: negative ML probability clamps to 0.0
    assert calculate_effective_recovery_probability(-0.5, strat, 0) == 0.0

    # Clamping: excessive ML probability clamps to <= 1.0
    assert calculate_effective_recovery_probability(2.5, strat, 0) <= 1.0

    # ESCALATE_TO_HUMAN and unknown strategy return 0.0
    assert calculate_effective_recovery_probability(0.95, "ESCALATE_TO_HUMAN", 0) == 0.0
    assert calculate_effective_recovery_probability(0.95, "UNKNOWN_STRATEGY", 0) == 0.0


def test_tool_specific_non_success_semantics():
    from app.services.tool_registry import (
        execute_payment_retry_simulator,
        execute_payment_link_simulator,
        execute_payment_method_update_simulator,
        execute_customer_notification_simulator,
        execute_incentive_offer_simulator,
        execute_human_escalation_tool,
    )

    # When ML probability = 0.0, verify strategy-specific non-success statuses
    res_retry, _, is_rec_retry = execute_payment_retry_simulator("rc1", "p1", 1000, 0.0)
    assert res_retry == "FAILED"
    assert is_rec_retry is False

    res_link, _, is_rec_link = execute_payment_link_simulator("rc2", "p2", "c2", 1000, 0.0)
    assert res_link == "PENDING_CUSTOMER_ACTION"
    assert is_rec_link is False

    res_alt, _, is_rec_alt = execute_payment_method_update_simulator("rc3", "c3", 1000, 0.0)
    assert res_alt == "PENDING_CUSTOMER_ACTION"
    assert is_rec_alt is False

    res_rem, _, is_rec_rem = execute_customer_notification_simulator("rc4", "c4", 1000, 0.0)
    assert res_rem == "NOTIFICATION_DISPATCHED"
    assert is_rec_rem is False

    res_inc, _, is_rec_inc = execute_incentive_offer_simulator("rc5", "c5", 1000, 0.0)
    assert res_inc == "PENDING_CUSTOMER_ACTION"
    assert is_rec_inc is False

    res_esc, _, is_rec_esc = execute_human_escalation_tool("rc6", "Manual escalation")
    assert res_esc == "ESCALATED"
    assert is_rec_esc is False


def test_customer_notification_dispatch_never_marks_recovered():
    from app.services.tool_registry import execute_customer_notification_simulator, dispatch_tool

    # Even with ML probability = 1.0, reminder dispatch is purely informational and leaves case pending
    res, meta, is_rec = execute_customer_notification_simulator("rc_rem", "cust_1", 50000, ml_probability=1.0)
    assert res == "NOTIFICATION_DISPATCHED"
    assert is_rec is False
    assert meta["effective_probability"] == 0.0

    res_disp, meta_disp, is_rec_disp = dispatch_tool(
        tool_name="customer_notification_simulator",
        case_id="rc_rem",
        payment_id="pay_rem",
        customer_id="cust_1",
        amount_paise=50000,
        ml_probability=1.0,
    )
    assert res_disp == "NOTIFICATION_DISPATCHED"
    assert is_rec_disp is False
