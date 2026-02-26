"""
Vectorizer — Bag of Words and TF-IDF feature extraction.
"""

import os
import joblib
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from src.utils.logger import logger

VECTORIZER_TYPES = {"bow": CountVectorizer, "tfidf": TfidfVectorizer}


def get_vectorizer(method: str = "tfidf", **kwargs):
    """
    Return an unfitted vectorizer instance.

    Parameters
    ----------
    method : str
        "tfidf" or "bow"
    """
    method = method.lower()
    if method not in VECTORIZER_TYPES:
        raise ValueError(f"Unknown method '{method}'. Choose from {list(VECTORIZER_TYPES)}")
    return VECTORIZER_TYPES[method](**kwargs)


def fit_and_save(X_train, method: str = "tfidf", path: str = "models/vectorizer.pkl", **kwargs):
    """
    Fit a vectorizer on *X_train* and persist it to *path*.
    Returns (vectorizer, X_train_transformed).
    """
    vec = get_vectorizer(method, **kwargs)
    X_transformed = vec.fit_transform(X_train)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(vec, path)
    logger.info("Fitted %s vectorizer (%d features) → saved to %s",
                method.upper(), X_transformed.shape[1], path)
    return vec, X_transformed


def load_vectorizer(path: str = "models/vectorizer.pkl"):
    """Load a previously saved vectorizer."""
    vec = joblib.load(path)
    logger.info("Loaded vectorizer from %s", path)
    return vec


def extract_security_matrix(texts: list):
    """
    Extract security features from a list of texts and return as a numeric matrix.
    Useful for combining with TF-IDF vectors using scipy.hstack.
    """
    import numpy as np
    from src.security.risk_scoring import calculate_security_risk
    
    matrix = []
    for text in texts:
        risk = calculate_security_risk(text)
        # Flattened feature vector
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
