"""
URL Extractor — Detect URLs, domains, and suspicious link patterns in email text.
"""

import re
from typing import List

# Improved URL detection regex (limited to protocol/www URLs to avoid ReDoS risk)
URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s<>'\"()]+")

_MAX_REGEX_INPUT_LENGTH = 8192
_DOMAIN_TLDS = {
    "com",
    "net",
    "org",
    "edu",
    "gov",
    "io",
    "biz",
    "info",
    "xyz",
    "top",
    "click",
    "gq",
    "tk",
    "ml",
    "ga",
    "cf",
}


def _extract_domain_like_tokens(text: str) -> List[str]:
    domain_like: List[str] = []
    for token in text.split():
        clean = token.strip(".,;:!?()[]{}<>\"'")
        lower = clean.lower()
        if not lower or lower.startswith(("http://", "https://", "www.")):
            continue
        if "." not in lower:
            continue
        parts = lower.split(".")
        if len(parts) < 2 or any(not part for part in parts):
            continue
        if any(
            not all(ch.isalnum() or ch == "-" for ch in part) for part in parts[:-1]
        ):
            continue
        if parts[-1] in _DOMAIN_TLDS:
            domain_like.append(clean)
    return domain_like


def extract_urls(text: str) -> List[str]:
    """Extract all URLs and domain-like strings from text."""
    if not text:
        return []
    bounded_text = text[:_MAX_REGEX_INPUT_LENGTH]
    matches = URL_PATTERN.findall(bounded_text)
    matches.extend(_extract_domain_like_tokens(bounded_text))
    return list(dict.fromkeys(matches))


def get_domain(url: str) -> str:
    """Extract domain part from a URL string."""
    domain = url.lower()
    if domain.startswith(("http://", "https://")):
        domain = domain.split("//")[1]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.split("/")[0].split("?")[0]
