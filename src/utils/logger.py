"""
Logger module — Structured rotating file handler for the application.
Logs API requests, predictions, and errors to logs/app.log.
"""

import logging
import os
import uuid
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def setup_logger(name: str = "email_classifier", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger with rotating file handler and console output."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

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
    import sys, io
    stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def generate_request_id() -> str:
    """Generate a unique request ID for structured logging."""
    return str(uuid.uuid4())[:8]


# Default application logger
logger = setup_logger()
