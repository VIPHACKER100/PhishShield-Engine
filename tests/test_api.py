"""Tests for the FastAPI application."""

import sys
import os
import warnings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

# Suppress httpx deprecation warning for TestClient
warnings.filterwarnings("ignore", category=DeprecationWarning, module="httpx")


@pytest.fixture
def client():
    from src.api.app import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_home_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "PhishShield Engine" in res.text


def test_dashboard_page(client):
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "Dashboard" in res.text


def test_predict_empty_text(client):
    res = client.post("/predict", json={"text": ""})
    assert res.status_code == 422  # validation error


def test_analytics(client):
    res = client.get("/analytics")
    assert res.status_code == 200


def test_register_and_login(client):
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    # Password meets policy: 8+ chars, digit, special character
    good_password = "Secure@99!"

    # Register
    res = client.post("/auth/register", json={"username": username, "password": good_password})
    assert res.status_code == 200
    data = res.json()
    assert "api_key" in data
    assert data["api_key"].startswith("pse_"), "API key should use the pse_ prefix"

    # Login succeeds with correct credentials
    res = client.post("/auth/login", json={"username": username, "password": good_password})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert "expires_in" in data

    # Bad login returns 401
    res = client.post("/auth/login", json={"username": username, "password": "wrong"})
    assert res.status_code == 401


def test_register_rejects_weak_password(client):
    """Passwords shorter than 8 chars or lacking digit/special chars must be rejected."""
    import uuid
    username = f"weakuser_{uuid.uuid4().hex[:8]}"

    # Too short
    res = client.post("/auth/register", json={"username": username, "password": "Ab1!"})
    assert res.status_code == 422

    # No digit
    res = client.post("/auth/register", json={"username": username, "password": "NoDigit!!"})
    assert res.status_code in (409, 422)

    # No special character
    res = client.post("/auth/register", json={"username": username, "password": "NoSpecial1"})
    assert res.status_code in (409, 422)


def test_account_lockout(client):
    """After LOGIN_MAX_ATTEMPTS consecutive failures the account is locked."""
    import uuid
    username = f"lockuser_{uuid.uuid4().hex[:8]}"
    good_password = "Locked@99!"

    # Register
    res = client.post("/auth/register", json={"username": username, "password": good_password})
    assert res.status_code == 200

    # Exhaust the default 5 attempts
    for _ in range(5):
        res = client.post("/auth/login", json={"username": username, "password": "WrongPass!1"})
        assert res.status_code == 401

    # Next attempt should still return 401 (account locked, same generic error)
    res = client.post("/auth/login", json={"username": username, "password": good_password})
    assert res.status_code == 401


def test_password_reset_no_enumeration(client):
    """password-reset-request always returns 200, even for unknown usernames."""
    res = client.post("/auth/password-reset-request", json={"username": "nonexistent_user_xyz"})
    assert res.status_code == 200
    data = res.json()
    assert "detail" in data
    # _dev_token should be None for unknown users — not an error
    assert data.get("_dev_token") is None


def test_password_reset_full_flow(client):
    """Request a reset token, then use it to set a new password."""
    import uuid
    username = f"resetuser_{uuid.uuid4().hex[:8]}"
    original_password = "Original@1!"
    new_password = "NewSecure@2!"

    # Register
    client.post("/auth/register", json={"username": username, "password": original_password})

    # Request reset token
    res = client.post("/auth/password-reset-request", json={"username": username})
    assert res.status_code == 200
    token = res.json().get("_dev_token")
    assert token is not None

    # Reset password
    res = client.post("/auth/password-reset", json={
        "username": username,
        "token": token,
        "new_password": new_password,
    })
    assert res.status_code == 200

    # Old password should no longer work
    res = client.post("/auth/login", json={"username": username, "password": original_password})
    assert res.status_code == 401

    # New password should work
    res = client.post("/auth/login", json={"username": username, "password": new_password})
    assert res.status_code == 200
    assert "token" in res.json()


def test_password_reset_invalid_token(client):
    """An invalid reset token must be rejected."""
    import uuid
    username = f"badtoken_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={"username": username, "password": "ValidPwd@1!"})

    res = client.post("/auth/password-reset", json={
        "username": username,
        "token": "not-a-real-token",
        "new_password": "AnotherPwd@2!",
    })
    assert res.status_code == 400
