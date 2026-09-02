import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

# For local dev, use SQLite. In production, set DATABASE_URL to a PostgreSQL URI.
# Example: postgresql://user:pass@host:5432/dbname (requires psycopg2-binary)
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/app.db")

# SQLite requires check_same_thread=False for FastAPI's threaded usage.
# PostgreSQL (psycopg2) does not accept this argument.
_connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # --- Security fields ---
    # Optional email address (for password reset / future email verification)
    email = Column(String, unique=True, index=True, nullable=True)
    # Whether the user's email has been verified (feature-flagged; not enforced at login by default)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    # Consecutive failed login counter; reset to 0 on successful authentication
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    # When set, the account is locked until this UTC timestamp
    locked_until = Column(DateTime, nullable=True)
    # SHA-256 hash of a one-time password-reset token (never store the raw token)
    password_reset_token_hash = Column(String, nullable=True)
    # When the password-reset token expires (UTC)
    password_reset_expires = Column(DateTime, nullable=True)

    logs = relationship("UsageLog", back_populates="user")

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String)
    request_body = Column(Text)
    response_body = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="logs")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    email_text = Column(Text, nullable=False)
    predicted_label = Column(String, nullable=False)
    correct_label = Column(String, nullable=False)
    model_used = Column(String, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
