from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from app.main import app
from app.core.config import settings
import app.core.security as sec

client = TestClient(app)
TEST_SECRET_KEY = "test_super_secret_key_at_least_32_bytes_long_12345"


def create_test_token(sub="merchant_user_123", email="merchant@example.com", expires_delta=timedelta(hours=1), secret=TEST_SECRET_KEY):
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    if secret:
        return jwt.encode(payload, secret, algorithm="HS256")
    else:
        # Create unverified mock token
        h = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        import base64, json
        p = base64.b64encode(json.dumps(payload, default=str).encode()).decode().rstrip("=")
        return f"{h}.{p}.invalidsignature"


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


def test_production_mode_jwt_enforcement(monkeypatch):
    """Verifies that in production mode, unsigned/misconfigured JWTs are strictly rejected."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", None)
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "SUPABASE_JWKS_URL", None)
    sec._jwks_client = None
    
    token = create_test_token()
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 500
    assert "missing SUPABASE_URL" in resp.json()["detail"]

    # 2. Production mode with wrong secret signature -> 401 unauthorized
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "correct_production_secret_key_123456789")
    bad_token = create_test_token(secret="wrong_secret_key_987654321")
    resp2 = client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert resp2.status_code == 401

    # 3. Production mode with correct secret signature -> 200 authorized
    good_token = create_test_token(secret="correct_production_secret_key_123456789")
    resp3 = client.get("/auth/me", headers={"Authorization": f"Bearer {good_token}"})
    assert resp3.status_code == 200
    assert resp3.json()["merchant_id"] == "merchant_user_123"


def test_supabase_ecc_jwks_asymmetric_verification(monkeypatch):
    """
    Verifies that Supabase's current asymmetric ECC P-256 (ES256) signing keys
    are cryptographically verified using the JWKS key matching the token's kid.
    """
    # Generate an EC P-256 keypair simulating Supabase Auth signing key
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    kid = "test-supabase-ecc-key-id-12345"
    headers = {"kid": kid, "alg": "ES256"}
    payload = {
        "sub": "merchant_supabase_ecc_999",
        "email": "ecc_merchant@saas.com",
        "role": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    # Encode with ES256
    valid_ecc_token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

    # Mock PyJWKClient to return public key for kid
    class MockSigningKey:
        def __init__(self, key):
            self.key = key

    class MockJWKClient:
        def get_signing_key_from_jwt(self, token_str):
            h = jwt.get_unverified_header(token_str)
            if h.get("kid") == kid:
                return MockSigningKey(public_key)
            raise jwt.PyJWKClientError(f"Unable to find key {h.get('kid')}")

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://mockproject.supabase.co")
    monkeypatch.setattr(sec, "get_jwks_client", lambda: MockJWKClient())

    # 1. Valid ECC token with matching JWKS key -> 200 OK
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {valid_ecc_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["merchant_id"] == "merchant_supabase_ecc_999"
    assert data["email"] == "ecc_merchant@saas.com"

    # 2. Token signed with wrong EC key -> 401 Signature verification failed
    other_private_key = ec.generate_private_key(ec.SECP256R1())
    tampered_ecc_token = jwt.encode(payload, other_private_key, algorithm="ES256", headers=headers)
    resp_tampered = client.get("/auth/me", headers={"Authorization": f"Bearer {tampered_ecc_token}"})
    assert resp_tampered.status_code == 401
    assert "signature" in resp_tampered.json()["detail"].lower()

    # 3. Token with unknown kid -> 401 Key not found
    unknown_kid_token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "unknown-kid", "alg": "ES256"})
    resp_unknown = client.get("/auth/me", headers={"Authorization": f"Bearer {unknown_kid_token}"})
    assert resp_unknown.status_code == 401
