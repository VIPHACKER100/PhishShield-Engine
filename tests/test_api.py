"""Tests for the FastAPI application."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.api.app import app
    return TestClient(app)


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_home_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Email Spam Classifier" in res.text


def test_dashboard_page(client):
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "Dashboard" in res.text


def test_predict_empty_text(client):
    res = client.post("/predict", json={"email_text": ""})
    assert res.status_code == 422  # validation error


def test_analytics(client):
    res = client.get("/analytics")
    assert res.status_code == 200


def test_register_and_login(client):
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:8]}"

    # Register
    res = client.post("/auth/register", json={"username": username, "password": "testpass123"})
    assert res.status_code == 200
    data = res.json()
    assert "api_key" in data

    # Login
    res = client.post("/auth/login", json={"username": username, "password": "testpass123"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data

    # Bad login
    res = client.post("/auth/login", json={"username": username, "password": "wrong"})
    assert res.status_code == 401
