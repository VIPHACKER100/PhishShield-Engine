"""
Logger module — Structured rotating file handlers for application and security audit logs.
Logs general API traffic to logs/app.log and security events to logs/security_audit.log.
"""

import logging
import os
import sys
import io
import uuid
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
SECURITY_LOG_FILE = os.path.join(LOG_DIR, "security_audit.log")


def setup_logger(name: str = "email_classifier", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger with rotating file handler and console output."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger_inst = logging.getLogger(name)
    if logger_inst.handlers:
        return logger_inst

    logger_inst.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(request_id)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        defaults={"request_id": "N/A"},
    )

    # Rotating file handler (5 MB, keep 5 backups)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler — use UTF-8 to avoid Windows cp1252 encoding errors
    stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger_inst.addHandler(file_handler)
    logger_inst.addHandler(console_handler)

    return logger_inst


def setup_security_logger(name: str = "security_audit", level: int = logging.INFO) -> logging.Logger:
    """Configure and return dedicated security audit logger writing to logs/security_audit.log."""
    os.makedirs(LOG_DIR, exist_ok=True)

    sec_logger = logging.getLogger(name)
    if sec_logger.handlers:
        return sec_logger

    sec_logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [SECURITY] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler (10 MB, keep 10 backups)
    file_handler = RotatingFileHandler(SECURITY_LOG_FILE, maxBytes=10_000_000, backupCount=10, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    sec_logger.addHandler(file_handler)
    sec_logger.addHandler(console_handler)

    return sec_logger


def generate_request_id() -> str:
    """Generate a unique request ID for structured logging."""
    return str(uuid.uuid4())[:8]


def log_security_event(event_type: str, client_ip: str, username: str = "anonymous", detail: str = ""):
    """Convenience helper to record structured security audit events."""
    security_logger.info(
        "EVENT=%s IP=%s USER=%s DETAIL=%s",
        event_type, client_ip, username, detail
    )


# Default application loggers
logger = setup_logger()
security_logger = setup_security_logger()
