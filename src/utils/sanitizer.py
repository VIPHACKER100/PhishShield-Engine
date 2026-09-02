"""
Input Validation and Sanitization Utility
Provides centralized functions to sanitize raw input text and validate strict
input types for usernames, domains, tokens, model names, and labels.
"""

import re
import html
from typing import Optional

# Regex Patterns
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
_DOMAIN_RE = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$")
_TOKEN_RE = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")
_ALLOWED_MODELS = {"naive_bayes", "svm", "ensemble", "transformers", "deep_learning", "unknown"}
_ALLOWED_LABELS = {"spam", "ham"}

# Control Character Pattern (preserves \n, \r, \t, removes ASCII control chars 0-31 except 9,10,13 and 127)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(text: str, max_length: int = 50_000) -> str:
    """
    Sanitize raw text payload:
    1. Remove null bytes and non-printable control characters.
    2. HTML-escape tags (<script>, <iframe>, etc.) to prevent XSS.
    3. Truncate to max_length.
    """
    if not text:
        return ""
    # Strip null bytes and harmful control chars
    clean = _CONTROL_CHAR_RE.sub("", text)
    # HTML escape tags to neutralize XSS
    clean = html.escape(clean)
    # Truncate
    return clean[:max_length].strip()


def validate_username(username: str) -> str:
    """
    Validate username string:
    - 3 to 50 characters long
    - Alphanumeric, underscores, hyphens only
    Raises ValueError if invalid.
    """
    if not username or not isinstance(username, str):
        raise ValueError("Username is required.")
    stripped = username.strip()
    if not _USERNAME_RE.match(stripped):
        raise ValueError(
            "Username must be 3-50 characters long and contain only letters, numbers, underscores, or hyphens."
        )
    return stripped


def validate_domain(domain: str) -> str:
    """
    Validate domain name format (e.g. example.com, bad-site.net).
    Raises ValueError if invalid.
    """
    if not domain or not isinstance(domain, str):
        raise ValueError("Domain is required.")
    clean = domain.strip().lower()
    if not _DOMAIN_RE.match(clean):
        raise ValueError("Invalid domain name format. Must be a valid FQDN (e.g. malicious-site.com).")
    return clean


def validate_token(token: str) -> str:
    """
    Validate single-use token or API key structure.
    Raises ValueError if invalid.
    """
    if not token or not isinstance(token, str):
        raise ValueError("Token is required.")
    clean = token.strip()
    if not _TOKEN_RE.match(clean):
        raise ValueError("Invalid token format.")
    return clean


def validate_model_name(name: Optional[str]) -> Optional[str]:
    """
    Validate model name against allowed whitelist.
    """
    if name is None or name == "":
        return None
    clean = name.strip().lower()
    if clean not in _ALLOWED_MODELS:
        raise ValueError(f"Invalid model name '{name}'. Allowed models: {', '.join(sorted(_ALLOWED_MODELS))}")
    return clean


def validate_label(label: str) -> str:
    """
    Validate prediction or ground-truth label against allowed whitelist ('spam' or 'ham').
    """
    if not label or not isinstance(label, str):
        raise ValueError("Label is required.")
    clean = label.strip().lower()
    if clean not in _ALLOWED_LABELS:
        raise ValueError(f"Invalid label '{label}'. Label must be 'spam' or 'ham'.")
    return clean
