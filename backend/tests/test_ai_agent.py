from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from app.main import app
from app.database.session import init_db, SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.audit_event import AuditEvent
from app.services.ai_agent_service import (
    evaluate_recovery_strategy,
    validate_state_transition,
    execute_recovery_workflow,
    ALLOWED_STRATEGIES,
    STRATEGY_TOOL_MAPPING,
)
from app.services.tool_registry import dispatch_tool, ALLOWED_TOOLS

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


def test_strategy_allowlist_count_and_items():
    assert len(ALLOWED_STRATEGIES) == 6
    assert set(ALLOWED_STRATEGIES) == {
        "RETRY_PAYMENT",
        "CREATE_PAYMENT_LINK",
        "ALTERNATE_PAYMENT_METHOD",
        "SEND_REMINDER",
        "OFFER_INCENTIVE",
        "ESCALATE_TO_HUMAN",
    }


def test_tool_registry_count_and_items():
    assert len(ALLOWED_TOOLS) == 6
    assert set(ALLOWED_TOOLS) == {
        "payment_retry_simulator",
        "payment_link_simulator",
        "payment_method_update_simulator",
        "customer_notification_simulator",
        "incentive_offer_simulator",
        "human_escalation_tool",
    }


def test_disallowed_tool_rejection():
    with pytest.raises(ValueError, match="not in the allowlisted tool registry"):
        dispatch_tool(
            tool_name="unrestricted_sql_executor",
            case_id="rec_1",
            payment_id="pay_1",
            customer_id="C1",
            amount_paise=1000,
            ml_probability=0.8,
        )


def test_state_machine_transition_validation():
    assert validate_state_transition("FAILED", "ANALYZING") is True
    assert validate_state_transition("ANALYZING", "ACTION_SELECTED") is True
    assert validate_state_transition("ACTION_SELECTED", "ACTION_EXECUTED") is True
    assert validate_state_transition("ACTION_EXECUTED", "RECOVERED") is True
    # Invalid jump directly from FAILED to RECOVERED must be rejected
    assert validate_state_transition("FAILED", "RECOVERED") is False
    # Cannot transition out of terminal RECOVERED state
    assert validate_state_transition("RECOVERED", "FAILED") is False


def test_max_attempts_guardrail_escalation():
    cust = Customer(id="C_MAX", merchant_id="m1", demo_name="Max Corp", subscription_value=199900, tenure=12, activity_score=0.8)
    pay = Payment(id="p_max", merchant_id="m1", customer_id="C_MAX", amount=199900, currency="INR", payment_method="card", status="failed")

    # Test attempts 0, 1, 2, 3
    rec0 = RecoveryCase(id="r0", merchant_id="m1", payment_id="p_max", attempt_count=0, status="FAILED")
    strat0, _, _ = evaluate_recovery_strategy(cust, pay, rec0, ml_probability=0.90)
    assert strat0 != "ESCALATE_TO_HUMAN"

    rec3 = RecoveryCase(id="r3", merchant_id="m1", payment_id="p_max", attempt_count=3, status="FAILED")
    strat3, reason3, _ = evaluate_recovery_strategy(cust, pay, rec3, ml_probability=0.90)
    assert strat3 == "ESCALATE_TO_HUMAN"
    assert "Maximum automatic retry threshold reached" in reason3


def test_simulator_success_and_failure_fidelity():
    # Probability = 1.0 must yield success
    res_succ, meta_succ, is_succ = dispatch_tool("payment_retry_simulator", "rc1", "p1", "c1", 1000, 1.0)
    assert res_succ == "SUCCESS"
    assert is_succ is True
    assert meta_succ["demo"] is True

    # Probability = 0.0 must yield failure
    res_fail, meta_fail, is_fail = dispatch_tool("payment_retry_simulator", "rc2", "p2", "c2", 1000, 0.0)
    assert res_fail == "FAILED"
    assert is_fail is False


def test_execute_recovery_workflow_c1024():
    db = SessionLocal()
    try:
        # Reset C1024 case to FAILED for clean test execution
        case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1024_fail").first()
        if case:
            case.status = "FAILED"
            case.attempt_count = 0
            case.recovered_amount = 0
            db.query(RecoveryAction).filter(RecoveryAction.recovery_case_id == "rec_c1024_fail").delete()
            db.query(AuditEvent).filter(AuditEvent.entity_id == "rec_c1024_fail").delete()
            db.commit()

        res = execute_recovery_workflow(db, recovery_case_id="rec_c1024_fail", merchant_id="merchant_default")
        assert res["recovery_case_id"] == "rec_c1024_fail"
        assert res["customer_id"] == "C1024"
        assert res["selected_strategy"] in ALLOWED_STRATEGIES
        assert res["tool_invoked"] in ALLOWED_TOOLS
        assert res["current_status"] in ["RECOVERED", "ACTION_EXECUTED", "ESCALATED"]

        # Check action was recorded in database
        action = db.query(RecoveryAction).filter(RecoveryAction.recovery_case_id == "rec_c1024_fail").order_by(RecoveryAction.executed_at.desc()).first()
        assert action is not None
        assert action.action_type in ALLOWED_STRATEGIES

        # Check audit event was recorded in database
        audit = db.query(AuditEvent).filter(AuditEvent.entity_id == "rec_c1024_fail").order_by(AuditEvent.created_at.desc()).first()
        assert audit is not None
        assert "RECOVERY_" in audit.event_type
    finally:
        db.close()


def test_duplicate_recovery_prevention():
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).filter(RecoveryCase.status == "RECOVERED").first()
        if case:
            with pytest.raises(ValueError, match="already in terminal state"):
                execute_recovery_workflow(db, recovery_case_id=case.id, merchant_id=case.merchant_id)
    finally:
        db.close()


def test_api_recover_case_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header()
        db = SessionLocal()
        case = db.query(RecoveryCase).filter(RecoveryCase.status == "FAILED").first()
        case_id = case.id if case else "rec_c1024_fail"
        db.close()

        res = client.post(f"/ai/recover/{case_id}", headers=headers)
        assert res.status_code in [200, 400]
        if res.status_code == 200:
            data = res.json()
            assert "selected_strategy" in data
            assert "tool_invoked" in data
            assert data["demo"] is True


def test_api_ai_decisions_feed():
    with TestClient(app) as client:
        headers = get_auth_header()
        res = client.get("/ai/decisions?limit=50", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify no memory-learning events leaked into decisions
        for item in data:
            assert item["event_type"] != "AGENT_MEMORY_LEARNED"
            assert not str(item["id"]).startswith("aud_mem_")
            assert item["actor"] in ["ai_recovery_agent_v1", "autonomous_simulator_engine_v1", "system", "ml_engine", "memory_engine"]

        event_types = [item["event_type"] for item in data]
        has_decision_event = any(t.startswith("RECOVERY_") or t.startswith("SIMULATOR_") for t in event_types)
        assert has_decision_event, "Decisions feed should include RECOVERY_* or SIMULATOR_* decision events."


def test_api_ai_decisions_multi_attempt_lifecycle_c1910():
    db = SessionLocal()
    try:
        from app.services.simulator_service import simulate_case_recovery
        # Reset and simulate multi-attempt lifecycle for rec_c1910_2
        case = db.query(RecoveryCase).filter(RecoveryCase.id == "rec_c1910_2").first()
        if case:
            case.status = "FAILED"
            case.attempt_count = 0
            case.recovered_amount = 0
            case.selected_strategy = None
            db.commit()

        # Attempt 1: RETRY_PAYMENT -> FAILED
        res1 = simulate_case_recovery(db, recovery_case_id="rec_c1910_2", merchant_id="merchant_default", scenario="force_fail")
        assert res1["is_recovered"] is False

        # Attempt 2: ALTERNATE_PAYMENT_METHOD -> SUCCESS
        res2 = simulate_case_recovery(db, recovery_case_id="rec_c1910_2", merchant_id="merchant_default", scenario="force_success")
        assert res2["is_recovered"] is True

        with TestClient(app) as client:
            headers = get_auth_header()
            res = client.get("/ai/decisions?limit=50", headers=headers)
            assert res.status_code == 200
            data = res.json()

            c1910_events = [
                d for d in data
                if d.get("recovery_case_id") == "rec_c1910_2" or d.get("metadata", {}).get("customer_id") == "C1910"
            ]
            assert len(c1910_events) >= 2, "Both Attempt 1 and Attempt 2 should be returned in decisions feed."

            strategies = [d.get("metadata", {}).get("selected_strategy") or d.get("event_type") for d in c1910_events]
            assert any("RETRY_PAYMENT" in s or "ALTERNATE_PAYMENT_METHOD" in s for s in strategies)
            assert all(s is not None for s in strategies)
    finally:
        db.close()


def test_api_recovery_workflow_inspection():
    with TestClient(app) as client:
        headers = get_auth_header()
        res = client.get("/ai/recovery-case/rec_c1024_fail/workflow", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["case_id"] == "rec_c1024_fail"
        assert len(data["actions"]) > 0
        assert len(data["audit_events"]) > 0


def test_merchant_isolation_on_recovery():
    with TestClient(app) as client:
        # Unauthorized merchant B attempting to trigger merchant A case
        headers_b = get_auth_header(sub="unauthorized_merchant_b", email="b@other.com")
        res = client.post("/ai/recover/rec_c1024_fail", headers=headers_b)
        assert res.status_code == 400
        assert "not found or unauthorized" in res.json()["detail"].lower()
