from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from app.main import app
from app.database.session import init_db, SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.services.risk_engine_service import (
    calculate_merchant_risk_overview,
    compute_recoverability_weight,
    get_failure_reasons_breakdown,
    get_payment_methods_breakdown,
)

TEST_SECRET_KEY = "test_super_secret_key_at_least_32_bytes_long_12345"


def get_auth_header(sub="merchant_test_risk_01", email="risk@merchant.com"):
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module", autouse=True)
def setup_isolated_merchant_data():
    init_db()
    db = SessionLocal()
    try:
        # Create merchant A data
        mid_a = "merchant_test_risk_01"
        cust_a = Customer(
            id="C_RISK_01",
            merchant_id=mid_a,
            demo_name="Risk Test Corp A",
            subscription_value=200000,  # ₹2,000 in paise
            tenure=12,
            activity_score=0.85,
        )
        db.merge(cust_a)

        # Payment 1: ₹1,000 Failed (100000 paise)
        pay_1 = Payment(
            id="pay_risk_01",
            merchant_id=mid_a,
            customer_id="C_RISK_01",
            amount=100000,
            currency="INR",
            payment_method="card",
            status="failed",
            failure_reason="Card Declined (Insufficient Funds)",
        )
        # Payment 2: ₹2,000 Failed (200000 paise)
        pay_2 = Payment(
            id="pay_risk_02",
            merchant_id=mid_a,
            customer_id="C_RISK_01",
            amount=200000,
            currency="INR",
            payment_method="upi",
            status="failed",
            failure_reason="UPI Network Timeout",
        )
        # Payment 3: ₹3,000 Successful (300000 paise)
        pay_3 = Payment(
            id="pay_risk_03",
            merchant_id=mid_a,
            customer_id="C_RISK_01",
            amount=300000,
            currency="INR",
            payment_method="card",
            status="success",
            failure_reason=None,
        )
        db.merge(pay_1)
        db.merge(pay_2)
        db.merge(pay_3)

        # Create Merchant B data to test isolation
        mid_b = "merchant_test_risk_02"
        cust_b = Customer(
            id="C_RISK_02",
            merchant_id=mid_b,
            demo_name="Risk Test Corp B",
            subscription_value=500000,
            tenure=2,
            activity_score=0.20,
        )
        db.merge(cust_b)
        pay_b = Payment(
            id="pay_risk_b1",
            merchant_id=mid_b,
            customer_id="C_RISK_02",
            amount=500000,  # ₹5,000
            currency="INR",
            payment_method="netbanking",
            status="failed",
            failure_reason="Bank Server Unavailable",
        )
        db.merge(pay_b)
        db.commit()
    finally:
        db.close()


def test_recoverability_heuristic_weights():
    # Base for UPI Network Timeout = 0.85; activity 0.85 (+0.08); tenure 12 (+0.05) -> min(0.95, 0.98) = 0.95
    w_upi = compute_recoverability_weight("UPI Network Timeout", 0.85, 12)
    assert w_upi == 0.95

    # Low loyalty churn customer: Base Card Declined = 0.65; activity 0.20 (-0.15); tenure 1 (-0.10) -> 0.40
    w_churn = compute_recoverability_weight("Card Declined (Insufficient Funds)", 0.20, 1)
    assert round(w_churn, 2) == 0.40


def test_merchant_risk_overview_calculation():
    db = SessionLocal()
    try:
        overview = calculate_merchant_risk_overview(db, "merchant_test_risk_01")
        # Total volume: 100000 + 200000 + 300000 = 600000 paise (₹6,000)
        assert overview["total_volume_paise"] == 600000
        # Revenue at risk: 100000 + 200000 = 300000 paise (₹3,000)
        assert overview["revenue_at_risk_paise"] == 300000
        # Total counts: 3 attempts, 2 failed, 1 success
        assert overview["total_payment_count"] == 3
        assert overview["failed_payment_count"] == 2
        assert overview["success_payment_count"] == 1
        # Failure rate: 2 / 3 * 100 = 66.67%
        assert overview["failure_rate"] == 66.67
        # Estimated recoverable must be positive and <= revenue at risk
        assert 0 < overview["estimated_recoverable_paise"] <= overview["revenue_at_risk_paise"]
    finally:
        db.close()


def test_merchant_data_isolation():
    db = SessionLocal()
    try:
        overview_a = calculate_merchant_risk_overview(db, "merchant_test_risk_01")
        overview_b = calculate_merchant_risk_overview(db, "merchant_test_risk_02")

        # Merchant A should only see ₹3,000 at risk, Merchant B should see ₹5,000
        assert overview_a["revenue_at_risk_paise"] == 300000
        assert overview_b["revenue_at_risk_paise"] == 500000
    finally:
        db.close()


def test_empty_merchant_dataset():
    db = SessionLocal()
    try:
        empty_overview = calculate_merchant_risk_overview(db, "merchant_completely_empty")
        assert empty_overview["total_payment_count"] == 0
        assert empty_overview["revenue_at_risk_paise"] == 0
        assert empty_overview["estimated_recoverable_paise"] == 0
        assert empty_overview["failure_rate"] == 0.0
    finally:
        db.close()


def test_failure_reasons_breakdown_service():
    db = SessionLocal()
    try:
        reasons = get_failure_reasons_breakdown(db, "merchant_test_risk_01")
        assert len(reasons) == 2
        total_risk = sum(r["revenue_at_risk_paise"] for r in reasons)
        assert total_risk == 300000
    finally:
        db.close()


def test_payment_methods_breakdown_service():
    db = SessionLocal()
    try:
        methods = get_payment_methods_breakdown(db, "merchant_test_risk_01")
        assert len(methods) == 2
        card_method = next(m for m in methods if m["payment_method"] == "card")
        assert card_method["total_count"] == 2
        assert card_method["failed_count"] == 1
        assert card_method["failure_rate"] == 50.0
    finally:
        db.close()


def test_analytics_api_overview_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header("merchant_test_risk_01")
        res = client.get("/analytics/overview", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["revenue_at_risk_paise"] == 300000
        assert data["failed_payment_count"] == 2
        assert data["failure_rate"] == 66.67


def test_analytics_api_failure_reasons_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header("merchant_test_risk_01")
        res = client.get("/analytics/failure-reasons", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 2


def test_analytics_api_payment_methods_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header("merchant_test_risk_01")
        res = client.get("/analytics/payment-methods", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)


def test_analytics_api_trends_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header("merchant_test_risk_01")
        res = client.get("/analytics/trends?period=daily", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
