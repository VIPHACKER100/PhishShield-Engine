from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from src.utils.sanitizer import (
    sanitize_text,
    validate_username,
    validate_token,
    validate_model_name,
    validate_label,
)

MAX_TEXT_LENGTH = 50_000
MAX_HEADER_LENGTH = 10_000


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    model: Optional[str] = None
    headers: Optional[str] = Field(default="", max_length=MAX_HEADER_LENGTH)
    # Honeypot field — bots filling all inputs will populate this and be rejected
    bot_trap: Optional[str] = ""

    @field_validator("text")
    @classmethod
    def sanitise_body_text(cls, v: str) -> str:
        return sanitize_text(v, MAX_TEXT_LENGTH)

    @field_validator("headers")
    @classmethod
    def sanitise_headers_text(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return ""
        return sanitize_text(v, MAX_HEADER_LENGTH)

    @field_validator("model")
    @classmethod
    def check_model_name(cls, v: Optional[str]) -> Optional[str]:
        return validate_model_name(v)

    @field_validator("bot_trap")
    @classmethod
    def check_honeypot(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 0:
            raise ValueError("Bot activity detected via honeypot input.")
        return v


class BatchPredictRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    # Capped at max 50 emails per request to prevent bulk data scraping and resource exhaustion
    emails: list[str] = Field(..., min_length=1, max_length=50)
    model_name: Optional[str] = None

    @field_validator("emails")
    @classmethod
    def sanitise_batch_emails(cls, v: list[str]) -> list[str]:
        return [sanitize_text(email, MAX_TEXT_LENGTH) for email in v]

    @field_validator("model_name")
    @classmethod
    def check_batch_model_name(cls, v: Optional[str]) -> Optional[str]:
        return validate_model_name(v)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    # Minimum 8 chars enforced; maximum 128 chars protects bcrypt from CPU DoS
    password: str = Field(..., min_length=8, max_length=128)
    # Optional email — required for password reset flows
    email: Optional[EmailStr] = None
    # Honeypot field
    bot_trap: Optional[str] = ""

    @field_validator("username")
    @classmethod
    def check_username_format(cls, v: str) -> str:
        return validate_username(v)

    @field_validator("email")
    @classmethod
    def check_email_safety(cls, v: Optional[EmailStr]) -> Optional[EmailStr]:
        if v:
            s_val = str(v)
            if "\n" in s_val or "\r" in s_val or "\0" in s_val:
                raise ValueError("Email contains invalid characters.")
        return v

    @field_validator("bot_trap")
    @classmethod
    def check_honeypot(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 0:
            raise ValueError("Bot registration attempt detected.")
        return v


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def check_login_username(cls, v: str) -> str:
        return validate_username(v)


class PasswordResetRequestSchema(BaseModel):
    """Request a password-reset token to be sent out-of-band (e.g. email)."""

    username: str = Field(..., min_length=1, max_length=50)

    @field_validator("username")
    @classmethod
    def check_reset_username(cls, v: str) -> str:
        return validate_username(v)


class PasswordResetSchema(BaseModel):
    """Consume a password-reset token and set a new password."""

    username: str = Field(..., min_length=1, max_length=50)
    token: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def check_reset_user(cls, v: str) -> str:
        return validate_username(v)

    @field_validator("token")
    @classmethod
    def check_reset_token(cls, v: str) -> str:
        return validate_token(v)


class FeedbackRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    email_text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    predicted_label: str
    correct_label: str
    model_used: str = "unknown"

    @field_validator("email_text")
    @classmethod
    def sanitise_feedback_text(cls, v: str) -> str:
        return sanitize_text(v, MAX_TEXT_LENGTH)

    @field_validator("predicted_label")
    @classmethod
    def check_predicted_label(cls, v: str) -> str:
        return validate_label(v)

    @field_validator("correct_label")
    @classmethod
    def check_correct_label(cls, v: str) -> str:
        return validate_label(v)

    @field_validator("model_used")
    @classmethod
    def check_feedback_model_used(cls, v: str) -> str:
        res = validate_model_name(v)
        return res if res else "unknown"
