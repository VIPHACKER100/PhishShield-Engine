"""
Auth — Lightweight SQLAlchemy-based user management and JWT authentication.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import bcrypt  # type: ignore

from src.utils.logger import logger
from src.core.database import SessionLocal, User, UsageLog

JWT_SECRET = os.environ.get("JWT_SECRET", "email-classifier-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def init_db():
    """No-op. Database schema is initialized via src.core.database.init_db."""
    pass


def register_user(username: str, password: str) -> dict:
    """Register a new user in the database. Returns user info with API key."""
    session = SessionLocal()
    try:
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            raise ValueError(f"Username '{username}' already exists")

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        api_key = f"esc_{secrets.token_hex(24)}"
        
        user = User(
            username=username,
            password_hash=password_hash,
            api_key=api_key
        )
        session.add(user)
        session.commit()
        logger.info("Registered user: %s", username)
        return {"username": username, "api_key": api_key}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def authenticate_user(username: str, password: str) -> dict | None:
    """Validate credentials and return a JWT token."""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user is None:
            return None
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return None
        token = jwt.encode(
            {"sub": username, "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        return {"token": token, "username": username}
    finally:
        session.close()


def verify_token(token: str) -> str | None:
    """Decode JWT and return username, or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def verify_api_key(key: str) -> str | None:
    """Check API key against DB and return username, or None."""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(api_key=key).first()
        return user.username if user else None
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
            response_body=response_body
        )
        session.add(log)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Failed to log usage: %s", e)
    finally:
        session.close()
