from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from app.main import app
from app.database.session import init_db, SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase

# Initialize tables before running tests
init_db()


@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    init_db()
    db = SessionLocal()
    try:
        # Ensure test customer C1024 exists
        c1024 = db.query(Customer).filter(Customer.id == "C1024").first()
        if not c1024:
            c1024 = Customer(
                id="C1024",
                merchant_id="merchant_default",
                demo_name="Enterprise Cloud SaaS (C1024)",
                subscription_value=199900,
                tenure=18,
                activity_score=0.88,
            )
            db.add(c1024)
            db.commit()

        # Ensure a failed payment and recovery case exist
        pay = db.query(Payment).filter(Payment.id == "pay_test_seeded_001").first()
        if not pay:
            pay = Payment(
                id="pay_test_seeded_001",
                merchant_id="merchant_default",
                customer_id="C1024",
                amount=199900,
                currency="INR",
                payment_method="card",
                status="failed",
                failure_reason="Card Declined (Insufficient Funds)",
            )
            db.add(pay)
            db.flush()

            rec = RecoveryCase(
                id="rec_test_seeded_001",
                merchant_id="merchant_default",
                payment_id="pay_test_seeded_001",
                status="FAILED",
                attempt_count=0,
                expected_revenue=199900,
                recovered_amount=0,
            )
            db.add(rec)
            db.commit()
    finally:
        db.close()


def get_auth_header(sub="merchant_default", email="merchant@example.com"):
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, "secret_key_32_bytes_long_for_hmac_sha256", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_list_customers_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header()
        response = client.get("/customers?limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] > 0
        assert len(data["items"]) <= 10


def test_get_customer_by_id_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header()
        response = client.get("/customers/C1024", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "C1024"
        assert data["subscription_value"] == 199900
        assert data["tenure"] == 18


def test_list_payments_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header()
        response = client.get("/payments?limit=20", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] > 0


def test_list_payments_filter_by_status():
    with TestClient(app) as client:
        headers = get_auth_header()
        response = client.get("/payments?status=failed&limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert all(p["status"] == "failed" for p in data["items"])


def test_list_recovery_cases_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header()
        response = client.get("/recovery-cases?limit=15", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] > 0


def test_ingest_payment_event_endpoint():
    with TestClient(app) as client:
        headers = get_auth_header()
        event_payload = {
            "id": "pay_test_event_new_999",
            "customer_id": "C1024",
            "amount": 199900,
            "currency": "INR",
            "payment_method": "card",
            "status": "failed",
            "failure_reason": "Card Declined (Insufficient Funds)",
        }
        response = client.post("/payments/events", json=event_payload, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "pay_test_event_new_999"
        assert data["status"] == "failed"
        assert data["amount"] == 199900
