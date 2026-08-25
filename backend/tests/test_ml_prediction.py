from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from app.main import app
from app.database.session import init_db, SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.services.ml_prediction_service import (
    predict_recovery,
    get_metadata,
    get_model,
    build_feature_vector,
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


def test_model_artifact_loaded():
    model = get_model()
    assert model is not None
    meta = get_metadata()
    assert meta["model_version"] == "logistic-regression-v2"
    assert "metrics" in meta


def test_feature_vector_dimension():
    cust = Customer(
        id="C_TEST",
        merchant_id="merchant_default",
        demo_name="Test Corp",
        subscription_value=199900,
        tenure=12,
        activity_score=0.85,
    )
    pay = Payment(
        id="pay_test",
        merchant_id="merchant_default",
        customer_id="C_TEST",
        amount=199900,
        currency="INR",
        payment_method="card",
        status="failed",
        failure_reason="Card Declined (Insufficient Funds)",
    )
    vec = build_feature_vector(cust, pay, prior_success_count=10, prior_fail_count=1)
    assert vec.shape == (1, 18)


def test_predict_recovery_service_for_c1024():
    db = SessionLocal()
    try:
        res = predict_recovery(db, payment_id="pay_c1024_fail")
        assert res["payment_id"] == "pay_c1024_fail"
        assert res["customer_id"] == "C1024"
        assert 0.0 <= res["recovery_probability"] <= 1.0
        assert res["recovery_probability"] >= 0.70  # C1024 has high reliability
        assert res["model_version"] == "logistic-regression-v2"
        assert len(res["factors"]) >= 2
    finally:
        db.close()


def test_prediction_api_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header()
        payload = {"payment_id": "pay_c1024_fail"}
        res = client.post("/ai/predict-recovery", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["customer_id"] == "C1024"
        assert "recovery_probability" in data
        assert "factors" in data
        assert data["model_version"] == "logistic-regression-v2"


def test_model_info_api_endpoint():
    with TestClient(app) as client:
        res = client.get("/ai/model-info")
        assert res.status_code == 200
        data = res.json()
        assert data["model_version"] == "logistic-regression-v2"
        assert data["model_type"] == "LogisticRegression"


def test_invalid_payment_prediction_error():
    with TestClient(app) as client:
        headers = get_auth_header()
        payload = {"payment_id": "pay_nonexistent_9999"}
        res = client.post("/ai/predict-recovery", json=payload, headers=headers)
        assert res.status_code == 404
