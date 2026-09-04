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
    try:
        # Verify non-C1024 cases remain strictly protected against terminal state rerun
        case = db.query(RecoveryCase).filter(RecoveryCase.id != "rec_c1024_fail").first()
        if case:
            case.status = "RECOVERED"
            db.commit()
            with pytest.raises(ValueError, match="already in terminal state"):
                simulate_case_recovery(db, recovery_case_id=case.id, merchant_id="merchant_default")
    finally:
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
