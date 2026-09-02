"""
IDOR Security Tests — Verify strict resource ownership checks on user logs and feedback endpoints.
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-idor-tests-32bytes!")
os.environ.setdefault("ENV", "dev")

from src.core.database import init_db

init_db()

from src.api.app import app

client = TestClient(app)


def create_user_and_login(username_prefix: str):
    u = f"{username_prefix}_{uuid.uuid4().hex[:8]}"
    pwd = "SecurePass@123"
    reg = client.post("/auth/register", json={"username": u, "password": pwd})
    assert reg.status_code == 200
    log = client.post("/auth/login", json={"username": u, "password": pwd})
    assert log.status_code == 200
    token = log.json()["token"]
    api_key = reg.json()["api_key"]
    return u, token, api_key


def test_user_profile_me():
    u, token, _ = create_user_and_login("me_user")
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["username"] == u


def test_idor_log_access():
    """User B cannot access User A's usage log."""
    userA, tokenA, keyA = create_user_and_login("userA")
    userB, tokenB, keyB = create_user_and_login("userB")

    # Generate a log for User A by calling predict with User A's token
    res = client.post(
        "/predict/batch",
        json={"emails": ["Phishing alert!"]},
        headers={"Authorization": f"Bearer {tokenA}"},
    )
    assert res.status_code == 200

    # Retrieve logs for User A
    logs_A = client.get(
        "/auth/logs", headers={"Authorization": f"Bearer {tokenA}"}
    ).json()
    assert len(logs_A) > 0
    log_id_A = logs_A[0]["id"]

    # User A can view their own log
    res_A = client.get(
        f"/auth/logs/{log_id_A}", headers={"Authorization": f"Bearer {tokenA}"}
    )
    assert res_A.status_code == 200
    assert res_A.json()["id"] == log_id_A

    # User B attempts to access User A's log by ID (IDOR Attempt)
    res_B = client.get(
        f"/auth/logs/{log_id_A}", headers={"Authorization": f"Bearer {tokenB}"}
    )
    assert (
        res_B.status_code == 404
    ), "User B should receive 404 Not Found when requesting User A's log"


def test_idor_feedback_access_and_deletion():
    """User B cannot access or delete User A's feedback."""
    userA, tokenA, _ = create_user_and_login("fb_userA")
    userB, tokenB, _ = create_user_and_login("fb_userB")

    # User A submits feedback
    fb_res = client.post(
        "/feedback",
        json={
            "email_text": "Verify your bank account immediately!",
            "predicted_label": "ham",
            "correct_label": "spam",
            "model_used": "svm",
        },
        headers={"Authorization": f"Bearer {tokenA}"},
    )
    assert fb_res.status_code == 200
    feedback_id_A = fb_res.json()["entry"]["id"]

    # User A can view their feedback
    res_get_A = client.get(
        f"/auth/feedback/{feedback_id_A}", headers={"Authorization": f"Bearer {tokenA}"}
    )
    assert res_get_A.status_code == 200
    assert res_get_A.json()["id"] == feedback_id_A

    # User B attempts to view User A's feedback (IDOR Read Attempt)
    res_get_B = client.get(
        f"/auth/feedback/{feedback_id_A}", headers={"Authorization": f"Bearer {tokenB}"}
    )
    assert (
        res_get_B.status_code == 404
    ), "User B should receive 404 Not Found when reading User A's feedback"

    # User B attempts to delete User A's feedback (IDOR Delete Attempt)
    res_del_B = client.delete(
        f"/auth/feedback/{feedback_id_A}", headers={"Authorization": f"Bearer {tokenB}"}
    )
    assert (
        res_del_B.status_code == 404
    ), "User B should receive 404 Not Found when deleting User A's feedback"

    # User A can delete their own feedback
    res_del_A = client.delete(
        f"/auth/feedback/{feedback_id_A}", headers={"Authorization": f"Bearer {tokenA}"}
    )
    assert res_del_A.status_code == 200
    assert res_del_A.json()["detail"] == "Feedback entry deleted successfully."
