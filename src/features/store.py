"""
Feature Store — Cache and reuse precomputed feature matrices.
"""

import os
import json
import joblib
from datetime import datetime, timezone
from src.utils.logger import logger

FEATURE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "features")
FEATURE_META = os.path.join(FEATURE_DIR, "feature_metadata.json")


def _load_meta() -> dict:
    os.makedirs(FEATURE_DIR, exist_ok=True)
    if os.path.exists(FEATURE_META):
        with open(FEATURE_META) as f:
            return json.load(f)
    return {}


def _save_meta(meta: dict):
    os.makedirs(FEATURE_DIR, exist_ok=True)
    with open(FEATURE_META, "w") as f:
        json.dump(meta, f, indent=2)


def save_features(X, name: str, dataset_version: str = "unknown", method: str = "tfidf") -> str:
    """
    Persist a feature matrix and record metadata.

    Parameters
    ----------
    X : sparse matrix
        The feature matrix.
    name : str
        Feature set name, e.g. "tfidf_train".
    dataset_version : str
        Which dataset version produced these features.
    method : str
        Vectorizer method used.

    Returns
    -------
    Path to saved feature file.
    """
    os.makedirs(FEATURE_DIR, exist_ok=True)
    path = os.path.join(FEATURE_DIR, f"{name}.pkl")
    joblib.dump(X, path)

    meta = _load_meta()
    meta[name] = {
        "path": path,
        "method": method,
        "dataset_version": dataset_version,
        "shape": list(X.shape),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_meta(meta)
    logger.info("Saved feature set '%s' (%s) → %s", name, X.shape, path)
    return path


def load_features(name: str):
    """Load a previously saved feature matrix."""
    meta = _load_meta()
    if name not in meta:
        raise KeyError(f"Feature set '{name}' not found in store. Available: {list(meta.keys())}")
    path = meta[name]["path"]
    X = joblib.load(path)
    logger.info("Loaded feature set '%s' from %s", name, path)
    return X


def list_features() -> dict:
    """List all feature sets in the store."""
    return _load_meta()


def feature_exists(name: str) -> bool:
    """Check if a feature set exists."""
    return name in _load_meta()
