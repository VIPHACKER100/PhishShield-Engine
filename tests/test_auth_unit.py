"""
Focused unit tests for src/api/auth.py.
These import auth functions directly, bypassing the full FastAPI app stack
(no prometheus, arq, or Redis dependencies required).
"""
import os
import sys
import uuid
import pytest

# Ensure project root on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use an in-memory SQLite DB for these tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-unit-tests-only!")
os.environ.setdefault("ENV", "dev")


def setup_module(module):
    """Create DB tables before any test in this module runs."""
    from src.core.database import init_db
    init_db()


from src.api import auth as auth_module

# Override constants to make lockout tests fast
auth_module.LOGIN_MAX_ATTEMPTS = 3
auth_module.LOGIN_LOCKOUT_MINUTES = 60  # lock for 60 min so tests catch it reliably


def unique_user():
    return f"user_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_success(self):
        u = unique_user()
        result = auth_module.register_user(u, "Valid@123")
        assert result["username"] == u
        assert result["api_key"].startswith("pse_")

    def test_register_duplicate_username_raises(self):
        u = unique_user()
        auth_module.register_user(u, "Valid@123")
        with pytest.raises(ValueError, match="already exists"):
            auth_module.register_user(u, "Valid@123")

    def test_register_password_too_short(self):
        with pytest.raises(ValueError, match="8 characters"):
            auth_module.register_user(unique_user(), "Sh@1")

    def test_register_password_no_digit(self):
        with pytest.raises(ValueError, match="digit"):
            auth_module.register_user(unique_user(), "NoDigit!!")

    def test_register_password_no_special(self):
        with pytest.raises(ValueError, match="special character"):
            auth_module.register_user(unique_user(), "NoSpecial1")

    def test_register_with_email(self):
        u = unique_user()
        result = auth_module.register_user(u, "Valid@123", email=f"{u}@example.com")
        assert result["username"] == u


# ---------------------------------------------------------------------------
# Authentication & lockout
# ---------------------------------------------------------------------------

class TestAuthentication:
    def test_login_success(self):
        u = unique_user()
        auth_module.register_user(u, "Login@123")
        result = auth_module.authenticate_user(u, "Login@123")
        assert result is not None
        assert "token" in result
        assert "expires_in" in result

    def test_login_wrong_password(self):
        u = unique_user()
        auth_module.register_user(u, "Login@123")
        assert auth_module.authenticate_user(u, "Wrong@999") is None

    def test_login_nonexistent_user(self):
        # Must return None (not raise) and not reveal user absence via timing
        assert auth_module.authenticate_user("ghost_user_xyz", "Any@Pass1") is None

    def test_account_lockout(self):
        u = unique_user()
        auth_module.register_user(u, "Lock@123")
        # Exhaust attempts (LOGIN_MAX_ATTEMPTS = 3 in this test)
        for _ in range(3):
            auth_module.authenticate_user(u, "Wrong@Pass1")
        # Even the correct password should now return None (account locked)
        assert auth_module.authenticate_user(u, "Lock@123") is None

    def test_verify_token_valid(self):
        u = unique_user()
        auth_module.register_user(u, "Token@123")
        result = auth_module.authenticate_user(u, "Token@123")
        username = auth_module.verify_token(result["token"])
        assert username == u

    def test_verify_token_invalid(self):
        assert auth_module.verify_token("not.a.real.token") is None

    def test_verify_api_key(self):
        u = unique_user()
        reg = auth_module.register_user(u, "ApiKey@123")
        username = auth_module.verify_api_key(reg["api_key"])
        assert username == u

    def test_verify_api_key_wrong(self):
        assert auth_module.verify_api_key("pse_notarealkey") is None


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

class TestPasswordReset:
    def test_reset_request_unknown_user_returns_none(self):
        # Returns None (caller surfaces generic response; no exception)
        result = auth_module.request_password_reset("no_such_user_xyz")
        assert result is None

    def test_full_reset_flow(self):
        u = unique_user()
        auth_module.register_user(u, "Orig@123")
        raw_token = auth_module.request_password_reset(u)
        assert raw_token is not None

        ok = auth_module.reset_password(u, raw_token, "NewPass@999")
        assert ok is True

        # Old password should no longer work
        assert auth_module.authenticate_user(u, "Orig@123") is None
        # New password should work
        assert auth_module.authenticate_user(u, "NewPass@999") is not None

    def test_invalid_token_rejected(self):
        u = unique_user()
        auth_module.register_user(u, "Tokn@1234")  # 9 chars, meets policy
        auth_module.request_password_reset(u)
        ok = auth_module.reset_password(u, "bogus-token-xyz", "NewPass@999")
        assert ok is False

    def test_token_single_use(self):
        u = unique_user()
        auth_module.register_user(u, "Once@123")
        raw_token = auth_module.request_password_reset(u)
        auth_module.reset_password(u, raw_token, "NewPass@999")
        # Second use of same token must fail
        ok = auth_module.reset_password(u, raw_token, "AnotherPass@888")
        assert ok is False

    def test_weak_new_password_rejected(self):
        u = unique_user()
        auth_module.register_user(u, "Strong@123")
        raw_token = auth_module.request_password_reset(u)
        with pytest.raises(ValueError):
            auth_module.reset_password(u, raw_token, "weak")
