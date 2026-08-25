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
    MEMORY_VERSION,
)
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
