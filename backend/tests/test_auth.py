from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
from app.main import app

client = TestClient(app)
TEST_SECRET_KEY = "test_super_secret_key_at_least_32_bytes_long_12345"


def create_test_token(sub="merchant_user_123", email="merchant@example.com", expires_delta=timedelta(hours=1)):
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")


def test_auth_me_unauthorized_without_token():
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_auth_me_unauthorized_with_malformed_token():
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert response.status_code == 401


def test_auth_me_unauthorized_with_expired_token():
    expired_token = create_test_token(expires_delta=timedelta(hours=-1))
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_auth_me_authorized_with_valid_token():
    valid_token = create_test_token(sub="merchant_test_456", email="owner@saas.com")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_id"] == "merchant_test_456"
    assert data["email"] == "owner@saas.com"
    assert data["role"] == "authenticated"


def test_auth_logout_endpoint():
    valid_token = create_test_token(sub="merchant_test_456", email="owner@saas.com")
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert response.json()["success"] is True
