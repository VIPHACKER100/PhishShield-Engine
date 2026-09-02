"""
Auth — Secure SQLAlchemy-based user management and JWT authentication.

Security properties enforced here:
  • bcrypt password hashing (auto work-factor via gensalt)
  • JWT secrets sourced exclusively from SecretsVault (env-first, no code-level defaults)
  • Short-lived JWTs (configurable, default 1 hour) with jti + iat claims
  • Generic error messages for login failures (prevents user enumeration)
  • Account lockout after N consecutive failed attempts
  • Constant-time API key comparison (hmac.compare_digest)
  • Password reset via single-use, time-limited, server-side-hashed tokens
"""

import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import bcrypt  # type: ignore

from src.utils.logger import logger
from src.utils.secrets import vault
from src.core.database import SessionLocal, User, UsageLog

# ---------------------------------------------------------------------------
# Configuration — tune via environment variables
# ---------------------------------------------------------------------------

JWT_SECRET: str = vault.get("JWT_SECRET")          # Must be set; vault raises in prod if absent
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_HOURS: int = int(os.environ.get("JWT_EXPIRY_HOURS", "1"))   # Default: 1 hour
LOGIN_MAX_ATTEMPTS: int = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_LOCKOUT_MINUTES: int = int(os.environ.get("LOGIN_LOCKOUT_MINUTES", "15"))
RESET_TOKEN_EXPIRY_HOURS: int = int(os.environ.get("RESET_TOKEN_EXPIRY_HOURS", "1"))

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_token(raw_token: str) -> str:
    """Return a SHA-256 hex digest of a raw token for safe DB storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _is_locked(user: User) -> bool:
    """Return True if the account is currently locked."""
    if user.locked_until is None:
        return False
    return datetime.now(timezone.utc) < user.locked_until.replace(tzinfo=timezone.utc)


from src.utils.logger import logger, log_security_event

def _record_failed_login(session, user: User, client_ip: str = "N/A") -> None:
    """Increment failure counter and lock the account when the threshold is exceeded."""
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= LOGIN_MAX_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        logger.warning(
            "Account '%s' locked for %d minutes after %d failed attempts.",
            user.username, LOGIN_LOCKOUT_MINUTES, user.failed_login_attempts,
        )
        log_security_event(
            "ACCOUNT_LOCKED",
            client_ip=client_ip,
            username=user.username,
            detail=f"Locked for {LOGIN_LOCKOUT_MINUTES} min after {user.failed_login_attempts} failed attempts"
        )
    session.commit()


def _reset_login_counter(session, user: User) -> None:
    """Clear failure counter and lockout on successful authentication."""
    user.failed_login_attempts = 0
    user.locked_until = None
    session.commit()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db():
    """No-op. Database schema is initialized via src.core.database.init_db."""
    pass


def register_user(username: str, password: str, email: str | None = None) -> dict:
    """
    Register a new user.

    Password policy (enforced here in addition to schema-level validation):
      • Minimum 8 characters
      • At least one digit
      • At least one special character

    Returns user info with the API key — this is the ONLY time the raw key is revealed.
    Callers should treat the returned api_key as a one-time secret.
    """
    # --- Password policy ---
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit.")
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        raise ValueError("Password must contain at least one special character.")

    session = SessionLocal()
    try:
        if session.query(User).filter_by(username=username).first():
            raise ValueError(f"Username '{username}' already exists.")
        if email and session.query(User).filter_by(email=email).first():
            raise ValueError("An account with this email already exists.")

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        api_key = f"pse_{secrets.token_hex(24)}"  # prefix pse_ = PhishShield Engine

        user = User(
            username=username,
            password_hash=password_hash,
            api_key=api_key,
            email=email,
            is_email_verified=False,
            failed_login_attempts=0,
        )
        session.add(user)
        session.commit()
        logger.info("Registered user: %s", username)
        # NOTE: api_key is returned once here. Treat it as a secret and store it safely.
        return {"username": username, "api_key": api_key}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def authenticate_user(username: str, password: str, client_ip: str = "N/A") -> dict | None:
    """
    Validate credentials and return a short-lived JWT token.

    Returns None for any authentication failure (no user found, wrong password,
    or locked account) — callers receive the same error to prevent user enumeration.
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()

        # If no user found, perform a dummy bcrypt check so timing is uniform
        # and does not reveal whether the username exists.
        if user is None:
            bcrypt.checkpw(password.encode(), bcrypt.hashpw(b"dummy", bcrypt.gensalt()))
            return None

        # Account lockout check
        if _is_locked(user):
            logger.warning("Login attempt on locked account: %s", username)
            log_security_event("AUTH_FAILURE", client_ip=client_ip, username=username, detail="Locked account login attempt")
            return None

        # Verify password
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            _record_failed_login(session, user, client_ip)
            return None

        # Successful login
        _reset_login_counter(session, user)

        jti = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "sub": username,
                "iat": now,
                "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
                "jti": jti,
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        return {"token": token, "username": username, "expires_in": JWT_EXPIRY_HOURS * 3600}
    finally:
        session.close()


def verify_token(token: str) -> str | None:
    """Decode a JWT and return the username (`sub` claim), or None if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def verify_api_key(key: str) -> str | None:
    """
    Check an API key against the DB and return the username, or None.

    Uses hmac.compare_digest for constant-time comparison to prevent timing attacks.
    """
    session = SessionLocal()
    try:
        # Fetch all users is impractical at scale; index on api_key is present.
        # We fetch the user by key prefix structure and then do a constant-time compare.
        user = session.query(User).filter_by(api_key=key).first()
        if user is None:
            return None
        # Constant-time comparison — both sides must be the same type/length encoding.
        if not hmac.compare_digest(user.api_key.encode(), key.encode()):
            return None
        return user.username
    finally:
        session.close()


def request_password_reset(username: str) -> str | None:
    """
    Generate a one-time password reset token for `username`.

    The raw token is returned to the caller (to be delivered out-of-band, e.g. via email).
    Only the SHA-256 hash is stored in the database.
    Always returns the same generic success message regardless of whether the user exists
    (callers should not expose whether a username is registered).

    Returns the raw token string, or None if the user was not found.
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user is None:
            # Return None but callers should surface a generic "email sent" response.
            return None

        raw_token = secrets.token_urlsafe(32)
        user.password_reset_token_hash = _hash_token(raw_token)
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
        session.commit()

        logger.info("Password reset token issued for user: %s", username)
        return raw_token
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_password(username: str, raw_token: str, new_password: str) -> bool:
    """
    Verify a password reset token and update the user's password.

    Returns True on success, False if the token is invalid or expired.
    """
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(c.isdigit() for c in new_password):
        raise ValueError("Password must contain at least one digit.")
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in new_password):
        raise ValueError("Password must contain at least one special character.")

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user is None:
            return False

        stored_hash = user.password_reset_token_hash
        expires = user.password_reset_expires

        if not stored_hash or not expires:
            return False

        # Check expiry
        if datetime.now(timezone.utc) > expires.replace(tzinfo=timezone.utc):
            logger.warning("Expired password reset token used for: %s", username)
            return False

        # Constant-time hash comparison
        if not hmac.compare_digest(_hash_token(raw_token), stored_hash):
            return False

        # Update password and clear reset fields
        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user.password_reset_token_hash = None
        user.password_reset_expires = None
        user.failed_login_attempts = 0
        user.locked_until = None
        session.commit()

        logger.info("Password successfully reset for user: %s", username)
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def log_usage(user_id: int | None, endpoint: str, request_body: str, response_body: str):
    """Log an API usage record."""
    session = SessionLocal()
    try:
        log = UsageLog(
            user_id=user_id,
            endpoint=endpoint,
            request_body=request_body,
            response_body=response_body,
        )
        session.add(log)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Failed to log usage: %s", e)
    finally:
        session.close()


def get_user_by_username(username: str) -> User | None:
    """Fetch User instance by username."""
    session = SessionLocal()
    try:
        return session.query(User).filter_by(username=username).first()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Ownership-checked resource access (IDOR Prevention)
# ---------------------------------------------------------------------------

def get_user_logs(user_id: int) -> list[dict]:
    """Retrieve usage logs strictly filtered by user_id."""
    session = SessionLocal()
    try:
        logs = session.query(UsageLog).filter_by(user_id=user_id).order_by(UsageLog.id.desc()).all()
        return [
            {
                "id": l.id,
                "endpoint": l.endpoint,
                "request_body": l.request_body,
                "response_body": l.response_body,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ]
    finally:
        session.close()


def get_user_log_by_id(log_id: int, user_id: int) -> dict | None:
    """
    Retrieve a specific usage log by log_id.
    Strictly verifies ownership: log.user_id == user_id. Returns None if not owned.
    """
    session = SessionLocal()
    try:
        log = session.query(UsageLog).filter_by(id=log_id, user_id=user_id).first()
        if log is None:
            return None
        return {
            "id": log.id,
            "user_id": log.user_id,
            "endpoint": log.endpoint,
            "request_body": log.request_body,
            "response_body": log.response_body,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
    finally:
        session.close()


def get_user_feedback_by_id(feedback_id: int, user_id: int) -> dict | None:
    """
    Retrieve a feedback record by feedback_id.
    Strictly verifies ownership: feedback.user_id == user_id. Returns None if not owned.
    """
    from src.core.database import Feedback as DBFeedback
    session = SessionLocal()
    try:
        fb = session.query(DBFeedback).filter_by(id=feedback_id, user_id=user_id).first()
        if fb is None:
            return None
        return {
            "id": fb.id,
            "user_id": fb.user_id,
            "email_text": fb.email_text,
            "predicted_label": fb.predicted_label,
            "correct_label": fb.correct_label,
            "model_used": fb.model_used,
            "timestamp": fb.timestamp.isoformat() if fb.timestamp else None,
        }
    finally:
        session.close()


def delete_user_feedback(feedback_id: int, user_id: int) -> bool:
    """
    Delete a feedback record by feedback_id.
    Strictly verifies ownership: feedback.user_id == user_id. Returns False if not owned.
    """
    from src.core.database import Feedback as DBFeedback
    session = SessionLocal()
    try:
        fb = session.query(DBFeedback).filter_by(id=feedback_id, user_id=user_id).first()
        if fb is None:
            return False
        session.delete(fb)
        session.commit()
        logger.info("Deleted feedback id=%s owned by user_id=%s", feedback_id, user_id)
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

