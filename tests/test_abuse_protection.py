"""
Abuse Protection & Bot Detection Unit Tests

Tests anti-bot middleware logic, honeypot schema validation, and batch size caps
WITHOUT importing the full FastAPI app stack (no ML model / joblib dependency needed).
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-abuse-tests-32bytes!")
os.environ.setdefault("ENV", "dev")


# ---------------------------------------------------------------------------
# Honeypot Field Validation (schema-level)
# ---------------------------------------------------------------------------


class TestHoneypotValidation:
    """PredictRequest and RegisterRequest bot_trap field must reject non-empty values."""

    def test_predict_request_empty_bot_trap_passes(self):
        from src.api.schemas import PredictRequest

        req = PredictRequest(text="Hello test email", bot_trap="")
        assert req.bot_trap == ""

    def test_predict_request_none_bot_trap_passes(self):
        from src.api.schemas import PredictRequest

        req = PredictRequest(text="Hello test email")
        assert req.bot_trap == ""

    def test_predict_request_populated_bot_trap_raises(self):
        from pydantic import ValidationError
        from src.api.schemas import PredictRequest

        with pytest.raises(ValidationError) as exc_info:
            PredictRequest(
                text="Hello test email", bot_trap="I am a bot filling all fields"
            )
        errors = exc_info.value.errors()
        assert any("Bot activity" in str(e) for e in errors)

    def test_register_request_populated_bot_trap_raises(self):
        from pydantic import ValidationError
        from src.api.schemas import RegisterRequest

        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="botuser",
                password="Secure@123",
                bot_trap="auto-filled by script",
            )
        errors = exc_info.value.errors()
        assert any("Bot" in str(e) for e in errors)

    def test_register_request_empty_bot_trap_passes(self):
        from src.api.schemas import RegisterRequest

        req = RegisterRequest(username="realuser", password="Secure@123", bot_trap="")
        assert req.bot_trap == ""


# ---------------------------------------------------------------------------
# Batch Size Cap (schema-level)
# ---------------------------------------------------------------------------


class TestBatchSizeCap:
    """BatchPredictRequest must reject lists exceeding 50 emails."""

    def test_batch_of_50_emails_passes(self):
        from src.api.schemas import BatchPredictRequest

        req = BatchPredictRequest(emails=["email body"] * 50)
        assert len(req.emails) == 50

    def test_batch_of_51_emails_raises(self):
        from pydantic import ValidationError
        from src.api.schemas import BatchPredictRequest

        with pytest.raises(ValidationError):
            BatchPredictRequest(emails=["email body"] * 51)

    def test_batch_of_1_email_passes(self):
        from src.api.schemas import BatchPredictRequest

        req = BatchPredictRequest(emails=["single email"])
        assert len(req.emails) == 1

    def test_empty_batch_raises(self):
        from pydantic import ValidationError
        from src.api.schemas import BatchPredictRequest

        with pytest.raises(ValidationError):
            BatchPredictRequest(emails=[])


# ---------------------------------------------------------------------------
# Bot User-Agent Blacklist Logic (unit test of detection logic)
# ---------------------------------------------------------------------------

_BOT_USER_AGENTS = {
    "sqlmap",
    "nikto",
    "nmap",
    "masscan",
    "gocurl",
    "bytespider",
    "zgrab",
    "libwww-perl",
    "python-urllib",
    "dirbuster",
    "w3af",
    "acunetix",
    "nessus",
    "openvas",
}


def _is_blacklisted_ua(user_agent: str) -> bool:
    """Mirror of app.py bot detection logic."""
    ua_lower = user_agent.lower()
    return any(bot in ua_lower for bot in _BOT_USER_AGENTS)


class TestBotUserAgentBlacklist:
    """Verify the bot User-Agent detection logic correctly classifies agents."""

    def test_sqlmap_detected(self):
        assert _is_blacklisted_ua("sqlmap/1.5.2#stable (http://sqlmap.org)") is True

    def test_nikto_detected(self):
        assert _is_blacklisted_ua("Mozilla/5.0 Nikto/2.1.6") is True

    def test_nmap_detected(self):
        assert _is_blacklisted_ua("Nmap Scripting Engine") is True

    def test_masscan_detected(self):
        assert _is_blacklisted_ua("masscan/1.0 teh internets") is True

    def test_bytespider_detected(self):
        assert _is_blacklisted_ua("Bytespider; spider-feedback@bytedance.com") is True

    def test_zgrab_detected(self):
        assert _is_blacklisted_ua("zgrab/0.x") is True

    def test_python_urllib_detected(self):
        assert _is_blacklisted_ua("python-urllib/3.9") is True

    def test_dirbuster_detected(self):
        assert _is_blacklisted_ua("DirBuster-1.0") is True

    def test_legitimate_chrome_allowed(self):
        assert (
            _is_blacklisted_ua(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
            is False
        )

    def test_legitimate_api_client_allowed(self):
        assert _is_blacklisted_ua("PhishShieldClient/1.0") is False

    def test_curl_legit_allowed(self):
        assert _is_blacklisted_ua("curl/7.64.1") is False

    def test_postman_allowed(self):
        assert _is_blacklisted_ua("PostmanRuntime/7.36.0") is False

    def test_empty_ua_not_blacklisted_separately(self):
        # Empty UA is handled by a separate check in middleware, not the blacklist
        assert _is_blacklisted_ua("") is False


# ---------------------------------------------------------------------------
# Middleware Path Matching Logic
# ---------------------------------------------------------------------------


class TestApiPathMatching:
    """Anti-bot middleware applies to specific API path prefixes only."""

    API_PREFIXES = (
        "/predict",
        "/auth/",
        "/analyze-security",
        "/export-report",
        "/feedback",
    )

    def _is_api_path(self, path: str) -> bool:
        return any(path.lower().startswith(prefix) for prefix in self.API_PREFIXES)

    def test_predict_is_api_path(self):
        assert self._is_api_path("/predict") is True

    def test_auth_is_api_path(self):
        assert self._is_api_path("/auth/login") is True

    def test_analyze_security_is_api_path(self):
        assert self._is_api_path("/analyze-security") is True

    def test_feedback_is_api_path(self):
        assert self._is_api_path("/feedback") is True

    def test_health_not_api_path(self):
        assert self._is_api_path("/health") is False

    def test_metrics_not_api_path(self):
        assert self._is_api_path("/metrics") is False

    def test_home_not_api_path(self):
        assert self._is_api_path("/") is False
