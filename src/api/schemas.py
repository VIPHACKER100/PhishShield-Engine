from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

MAX_TEXT_LENGTH = 50_000

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    model: Optional[str] = None
    headers: Optional[str] = ""
    # Honeypot field — bots filling all inputs will populate this and be rejected
    bot_trap: Optional[str] = ""

    @field_validator("text")
    @classmethod
    def sanitise(cls, v: str) -> str:
        return v.strip()

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

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    # Minimum 8 chars enforced; further complexity is checked in auth.register_user()
    password: str = Field(..., min_length=8, max_length=128)
    # Optional email — required for password reset flows
    email: Optional[EmailStr] = None
    # Honeypot field
    bot_trap: Optional[str] = ""

    @field_validator("bot_trap")
    @classmethod
    def check_honeypot(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 0:
            raise ValueError("Bot registration attempt detected.")
        return v

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

class PasswordResetRequestSchema(BaseModel):
    """Request a password-reset token to be sent out-of-band (e.g. email)."""
    username: str = Field(..., min_length=1, max_length=50)

class PasswordResetSchema(BaseModel):
    """Consume a password-reset token and set a new password."""
    username: str = Field(..., min_length=1, max_length=50)
    token: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

class FeedbackRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    email_text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    predicted_label: str
    correct_label: str
    model_used: str = "unknown"
