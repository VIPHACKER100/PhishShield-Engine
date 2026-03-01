"""
Train Models — Upgraded model registry with fast sklearn estimators.

Models
------
* naive_bayes         — MultinomialNB (fast baseline)
* logistic_regression — LogisticRegression (strong linear baseline)
* svm                 — LinearSVC (best linear for text)
* random_forest       — RandomForestClassifier  (via sparse-safe Pipeline)
* gradient_boosting   — HistGradientBoostingClassifier (sparse-safe Pipeline)
* lgbm                — LGBMClassifier (if lightgbm is installed)

Note on memory
--------------
Tree-based models are wrapped in a ``Pipeline[MaxAbsScaler → model]`` so
the sparse TF-IDF matrix is *never* densified.  MaxAbsScaler preserves
sparsity, keeping memory usage bounded.
"""

from __future__ import annotations

import os
import joblib
from typing import Callable
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MaxAbsScaler
from sklearn.base import BaseEstimator, TransformerMixin
from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Optional LightGBM
# ---------------------------------------------------------------------------
try:
    from lightgbm import LGBMClassifier
    _LGBM_AVAILABLE = True
except ImportError:
    _LGBM_AVAILABLE = False

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Factory functions — build estimators (some wrapped in sparse-safe Pipelines)
# ---------------------------------------------------------------------------

def _make_naive_bayes():
    return MultinomialNB(alpha=0.1)

def _make_logistic_regression():
    return LogisticRegression(C=5.0, solver="saga", max_iter=1000, random_state=42)

def _make_svm():
    # Wrap in CalibratedClassifierCV so predict_proba is available
    return CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=10_000), cv=3)

def _make_random_forest():
    # MaxAbsScaler preserves sparsity → no dense conversion needed
    return Pipeline([
        ("scaler", MaxAbsScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200, max_depth=30, min_samples_leaf=2,
            n_jobs=-1, random_state=42,
        )),
    ])

def _make_gradient_boosting():
    # HistGB requires dense arrays. We densify it inside the pipeline.
    return Pipeline([
        ("scaler", MaxAbsScaler()),
        ("dense", DenseTransformer()),
        ("clf", HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.1, max_leaf_nodes=63, random_state=42,
        )),
    ])


MODEL_FACTORIES: dict[str, callable] = {
    "naive_bayes": _make_naive_bayes,
    "logistic_regression": _make_logistic_regression,
    "svm": _make_svm,
    "random_forest": _make_random_forest,
    "gradient_boosting": _make_gradient_boosting,
}

# Keep an alias for backwards-compatibility
MODEL_REGISTRY = MODEL_FACTORIES

if _LGBM_AVAILABLE:
    def _make_lgbm():
        return Pipeline([
            ("scaler", MaxAbsScaler()),
            ("clf", LGBMClassifier(
                n_estimators=300, learning_rate=0.05, num_leaves=63,
                n_jobs=-1, random_state=42, verbosity=-1,
            )),
        ])
    MODEL_FACTORIES["lgbm"] = _make_lgbm


def split_data(X, y, test_size: float = 0.2, random_state: int = 42):
    """Stratified 80/20 train-test split (falls back to non-stratified if only 1 class)."""
    n_classes = len(set(y))
    if n_classes < 2:
        logger.warning(
            "Only 1 unique class found in labels ('%s'). "
            "Stratification skipped — consider using a labelled dataset for training.",
            next(iter(set(y))),
        )
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def train_model(X_train, y_train, model_name: str, params: dict | None = None):
    """
    Train a single model by name.

    Parameters
    ----------
    model_name : str
        Key in MODEL_FACTORIES.
    params : dict, optional
        Ignored (each factory has its own defaults).  Kept for API compatibility.

    Returns
    -------
    Fitted estimator.
    """
    if model_name not in MODEL_FACTORIES:
        raise ValueError(
            f"Unknown model '{model_name}'. Choose from {list(MODEL_FACTORIES)}"
        )

    model = MODEL_FACTORIES[model_name]()
    model.fit(X_train, y_train)
    logger.info("Trained %s", model_name)
    return model


def save_model(model, path: str):
    """Persist a trained model via joblib."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    joblib.dump(model, path)
    logger.info("Saved model → %s", path)


def load_model(path: str):
    """Load a persisted model."""
    model = joblib.load(path)
    logger.info("Loaded model from %s", path)
    return model


def train_all(X_train, y_train, model_dir: str = "models") -> dict:
    """
    Train *all* registered models and save them.

    Returns
    -------
    dict of {model_name: fitted_model}
    """
    trained: dict = {}
    for name in MODEL_REGISTRY:
        try:
            model = train_model(X_train, y_train, name)
            save_model(model, os.path.join(model_dir, f"{name}.pkl"))
            trained[name] = model
        except Exception as exc:  # pragma: no cover
            logger.warning("Skipping %s — training failed: %s", name, exc)
    return trained
