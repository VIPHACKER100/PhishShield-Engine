"""
Input Validation and Sanitization Unit Tests
Tests text sanitization, HTML/XSS escaping, null byte stripping, username regex validation,
domain validation, token validation, model whitelist enforcement, and schema validation.
"""

import os
import sys
import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.sanitizer import (
    sanitize_text,
    validate_username,
    validate_domain,
    validate_token,
    validate_model_name,
    validate_label,
)
from src.api.schemas import (
    PredictRequest,
    RegisterRequest,
    LoginRequest,
    PasswordResetSchema,
    FeedbackRequest,
)

# ---------------------------------------------------------------------------
# 1. Text Sanitization (XSS, Null Bytes, Control Chars)
# ---------------------------------------------------------------------------


class TestTextSanitization:
    def test_html_script_tags_escaped(self):
        raw = "Hello <script>alert('xss')</script> world!"
        sanitized = sanitize_text(raw)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in sanitized

    def test_iframe_tag_escaped(self):
        raw = "<iframe src='http://evil.com'></iframe>"
        sanitized = sanitize_text(raw)
        assert "<iframe" not in sanitized
        assert "&lt;iframe" in sanitized

    def test_null_bytes_stripped(self):
        raw = "admin\x00user\x00password"
        sanitized = sanitize_text(raw)
        assert "\x00" not in sanitized
        assert sanitized == "adminuserpassword"

    def test_control_characters_stripped(self):
        raw = "Line1\x07\x08\x0bLine2"
        sanitized = sanitize_text(raw)
        assert "\x07" not in sanitized
        assert "Line1Line2" in sanitized

    def test_newlines_preserved(self):
        raw = "Header: val\nBody line 1\r\nBody line 2"
        sanitized = sanitize_text(raw)
        assert "Header: val\nBody line 1\r\nBody line 2" in sanitized

    def test_max_length_truncation(self):
        raw = "A" * 100
        sanitized = sanitize_text(raw, max_length=10)
        assert len(sanitized) == 10
        assert sanitized == "A" * 10


# ---------------------------------------------------------------------------
# 2. Username Regex Validation
# ---------------------------------------------------------------------------


class TestUsernameValidation:
    def test_valid_usernames(self):
        assert validate_username("alice") == "alice"
        assert validate_username("user_123") == "user_123"
        assert validate_username("admin-user") == "admin-user"

    def test_sql_injection_attempt_rejected(self):
        with pytest.raises(ValueError, match="Username must be"):
            validate_username("admin' OR '1'='1")

    def test_sql_comment_injection_rejected(self):
        with pytest.raises(ValueError, match="Username must be"):
            validate_username("admin'--")

    def test_script_tag_username_rejected(self):
        with pytest.raises(ValueError, match="Username must be"):
            validate_username("<script>alert(1)</script>")

    def test_spaces_in_username_rejected(self):
        with pytest.raises(ValueError, match="Username must be"):
            validate_username("user name")

    def test_too_short_username_rejected(self):
        with pytest.raises(ValueError, match="Username must be"):
            validate_username("ab")

    def test_too_long_username_rejected(self):
        with pytest.raises(ValueError, match="Username must be"):
            validate_username("a" * 51)


# ---------------------------------------------------------------------------
# 3. Domain Validation
# ---------------------------------------------------------------------------


class TestDomainValidation:
    def test_valid_domains(self):
        assert validate_domain("example.com") == "example.com"
        assert validate_domain("SUB.DOMAIN.ORG") == "sub.domain.org"
        assert validate_domain("phishing-site.co.uk") == "phishing-site.co.uk"

    def test_invalid_domain_syntax(self):
        with pytest.raises(ValueError, match="Invalid domain name format"):
            validate_domain("not_a_domain")

    def test_spaces_in_domain_rejected(self):
        with pytest.raises(ValueError, match="Invalid domain name format"):
            validate_domain("example .com")

    def test_sql_injection_in_domain_rejected(self):
        with pytest.raises(ValueError, match="Invalid domain name format"):
            validate_domain("example.com'; DROP TABLE bad_domains;--")


# ---------------------------------------------------------------------------
# 4. Token & Whitelist Validation
# ---------------------------------------------------------------------------


class TestTokenAndWhitelistValidation:
    def test_valid_tokens(self):
        assert validate_token("abc123XYZ_.-") == "abc123XYZ_.-"

    def test_invalid_token_characters(self):
        with pytest.raises(ValueError, match="Invalid token format"):
            validate_token("token_with_spaces and 'quotes'")

    def test_valid_model_names(self):
        assert validate_model_name("naive_bayes") == "naive_bayes"
        assert validate_model_name("SVM") == "svm"
        assert validate_model_name("ensemble") == "ensemble"

    def test_invalid_model_name_rejected(self):
        with pytest.raises(ValueError, match="Invalid model name"):
            validate_model_name("arbitrary_exec_model")

    def test_valid_labels(self):
        assert validate_label("SPAM") == "spam"
        assert validate_label("ham") == "ham"

    def test_invalid_label_rejected(self):
        with pytest.raises(ValueError, match="Invalid label"):
            validate_label("malicious")


# ---------------------------------------------------------------------------
# 5. Schema Validation Integration
# ---------------------------------------------------------------------------


class TestSchemaValidationIntegration:
    def test_predict_request_escapes_html(self):
        req = PredictRequest(text="Check this <script>alert(1)</script>")
        assert "<script>" not in req.text
        assert "&lt;script&gt;" in req.text

    def test_register_request_rejects_sql_username(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="admin'--", password="Secure@Password1!")

    def test_register_request_rejects_email_newline(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                username="validuser",
                password="Secure@Password1!",
                email="test@example.com\r\nBcc: evil@hacker.io",
            )

    def test_login_request_rejects_invalid_username(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="user with spaces", password="password")

    def test_password_reset_rejects_malformed_token(self):
        with pytest.raises(ValidationError):
            PasswordResetSchema(
                username="validuser",
                token="token with spaces!",
                new_password="NewSecure@Pass1!",
            )

    def test_feedback_request_validates_labels(self):
        with pytest.raises(ValidationError):
            FeedbackRequest(
                email_text="test", predicted_label="unknown_label", correct_label="ham"
            )
