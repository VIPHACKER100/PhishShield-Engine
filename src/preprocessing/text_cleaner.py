"""
Text Cleaner — Preprocessing pipeline for email text.
"""

import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Ensure NLTK data is available
for _pkg in ("punkt", "punkt_tab", "stopwords"):
    nltk.download(_pkg, quiet=True)

_stop_words = set(stopwords.words("english"))
_stemmer = PorterStemmer()


def to_lowercase(text: str) -> str:
    return text.lower()


def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))


def remove_numbers(text: str) -> str:
    return re.sub(r"\d+", "", text)


def remove_stopwords(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in _stop_words]


def tokenize(text: str) -> list[str]:
    return text.split()


def stem_tokens(tokens: list[str]) -> list[str]:
    return [_stemmer.stem(t) for t in tokens]


def preprocess_text(text: str) -> str:
    """
    Full preprocessing pipeline:
    lowercase → remove punctuation → remove numbers →
    tokenize → remove stopwords → stem → rejoin.
    """
    text = to_lowercase(text)
    text = remove_punctuation(text)
    text = remove_numbers(text)
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    tokens = stem_tokens(tokens)
    return " ".join(tokens)


def preprocess_dataframe(df, text_column: str = "text") -> "pd.DataFrame":
    """Apply preprocessing to a DataFrame column and return a copy."""
    import pandas as pd  # noqa: local import to keep module lightweight

    df = df.copy()
    df[text_column] = df[text_column].astype(str).apply(preprocess_text)
    return df
