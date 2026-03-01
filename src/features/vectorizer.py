"""
Vectorizer — Upgraded TF-IDF and Bag-of-Words feature extraction.

Improvements over v1
--------------------
* ``sublinear_tf=True`` by default — log-normalises term frequencies,
  which helps heavily for email text.
* Character n-grams (``char``) added as an alternative to word n-grams —
  very effective against obfuscated spam.
* Bigram support (``ngram_range=(1, 2)``) captures short phrases.
* ``min_df`` / ``max_df`` filtering reduces vocabulary noise.
* ``max_features`` cap keeps memory under control on huge corpora.
"""

from __future__ import annotations

import os
import joblib
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Vectorizer catalogue
# ---------------------------------------------------------------------------

VECTORIZER_TYPES: dict[str, type] = {
    "bow": CountVectorizer,
    "tfidf": TfidfVectorizer,
    "tfidf_char": TfidfVectorizer,   # character n-gram variant
}

# Sensible defaults that work well for email phishing / spam detection
DEFAULT_KWARGS: dict[str, dict] = {
    "bow": {
        "ngram_range": (1, 2),
        "min_df": 2,
        "max_df": 0.95,
        "max_features": 100_000,
        "strip_accents": "unicode",
        "analyzer": "word",
    },
    "tfidf": {
        "ngram_range": (1, 2),
        "sublinear_tf": True,
        "min_df": 2,
        "max_df": 0.95,
        "max_features": 100_000,
        "strip_accents": "unicode",
        "analyzer": "word",
    },
    "tfidf_char": {
        # Character 3→5-grams: robust to typos, obfuscation, and short tokens
        "ngram_range": (3, 5),
        "sublinear_tf": True,
        "min_df": 5,
        "max_df": 0.95,
        "max_features": 80_000,
        "strip_accents": "unicode",
        "analyzer": "char_wb",
    },
}


def get_vectorizer(method: str = "tfidf", **kwargs):
    """
    Return an unfitted vectorizer instance.

    Parameters
    ----------
    method : str
        One of ``"tfidf"`` (default), ``"bow"``, or ``"tfidf_char"``.
    **kwargs
        Override any default parameter.
    """
    method = method.lower()
    if method not in VECTORIZER_TYPES:
        raise ValueError(
            f"Unknown method '{method}'. Choose from {list(VECTORIZER_TYPES)}"
        )
    merged = {**DEFAULT_KWARGS.get(method, {}), **kwargs}
    return VECTORIZER_TYPES[method](**merged)


def fit_and_save(
    X_train,
    method: str = "tfidf",
    path: str = "models/vectorizer.pkl",
    **kwargs,
):
    """
    Fit a vectorizer on *X_train* and persist it to *path*.

    Returns
    -------
    (vectorizer, X_train_sparse_matrix)
    """
    vec = get_vectorizer(method, **kwargs)
    X_transformed = vec.fit_transform(X_train)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    joblib.dump(vec, path)
    logger.info(
        "Fitted %s vectorizer — vocab=%d features, matrix=%s → saved to %s",
        method.upper(), X_transformed.shape[1],
        "×".join(str(d) for d in X_transformed.shape),
        path,
    )
    return vec, X_transformed


def load_vectorizer(path: str = "models/vectorizer.pkl"):
    """Load a previously saved vectorizer."""
    vec = joblib.load(path)
    logger.info("Loaded vectorizer from %s", path)
    return vec


# ---------------------------------------------------------------------------
# Security feature matrix (unchanged from v1)
# ---------------------------------------------------------------------------

def extract_security_matrix(texts: list):
    """
    Extract hand-crafted security features from a list of texts.
    Useful for combining with TF-IDF vectors using ``scipy.hstack``.
    """
    import numpy as np
    from src.security.risk_scoring import calculate_security_risk

    matrix = []
    for text in texts:
        risk = calculate_security_risk(text)
        feats = [
            risk["risk_score"] / 100.0,
            risk["security_flags"]["homograph"],
            risk["security_flags"]["mixed_script"],
            risk["security_flags"]["suspicious_url"],
            risk["security_flags"]["ip_url"],
            risk["details"]["urls"]["url_count"],
            risk["details"]["urls"]["max_subdomains"],
            risk["details"]["urls"]["has_shortener"],
            risk["details"]["scripts"]["latin_ratio"],
        ]
        matrix.append(feats)

    return np.array(matrix, dtype=float)
