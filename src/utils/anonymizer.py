"""
Anonymizer — Strip PII (names, emails, phone numbers) from text data.
"""

import re
from src.utils.logger import logger

# Regex patterns for common PII
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")

# Simple name pattern — capitalized words that look like names
# This is a heuristic; for production use a NER model
_NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b")


def anonymize_text(text: str) -> str:
    """
    Remove PII from text:
    - Email addresses → [EMAIL]
    - Phone numbers → [PHONE]
    - URLs → [URL]
    - Name-like patterns → [NAME]
    """
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _URL_RE.sub("[URL]", text)
    text = _NAME_RE.sub("[NAME]", text)
    return text


def anonymize_dataframe(df, text_column: str = "text"):
    """Apply anonymization to a DataFrame text column."""
    import pandas as pd
    df = df.copy()
    df[text_column] = df[text_column].astype(str).apply(anonymize_text)
    logger.info("Anonymized %d rows in column '%s'", len(df), text_column)
    return df
