"""
Auth — Lightweight SQLite-based user management and JWT authentication.
"""

import os
import sqlite3
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
import bcrypt  # type: ignore

from src.utils.logger import logger

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "auth.db")
JWT_SECRET = os.environ.get("JWT_SECRET", "email-classifier-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            endpoint TEXT,
            request_body TEXT,
            response_body TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()
    logger.info("Auth database initialised at %s", DB_PATH)


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def register_user(username: str, password: str) -> dict:
    """Register a new user. Returns user info with API key."""
    conn = _get_db()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    api_key = f"esc_{secrets.token_hex(24)}"
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, api_key, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, api_key, now),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Username '{username}' already exists")
    conn.close()
    logger.info("Registered user: %s", username)
    return {"username": username, "api_key": api_key}


def authenticate_user(username: str, password: str) -> dict | None:
    """Validate credentials and return a JWT token."""
    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row is None:
        return None
    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return None
    token = jwt.encode(
        {"sub": username, "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {"token": token, "username": username}


def verify_token(token: str) -> str | None:
    """Decode JWT and return username, or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def verify_api_key(key: str) -> str | None:
    """Check API key against DB and return username, or None."""
    conn = _get_db()
    row = conn.execute("SELECT username FROM users WHERE api_key = ?", (key,)).fetchone()
    conn.close()
    return row["username"] if row else None


def log_usage(user_id: int | None, endpoint: str, request_body: str, response_body: str):
    """Log an API usage record."""
    conn = _get_db()
    conn.execute(
        "INSERT INTO usage_logs (user_id, endpoint, request_body, response_body, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, endpoint, request_body, response_body, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


# Auto-init on import
init_db()
