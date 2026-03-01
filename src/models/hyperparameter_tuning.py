"""
Hyperparameter Tuning — Upgraded with RandomizedSearchCV + broader grids.

Changes vs. v1
--------------
* Uses ``RandomizedSearchCV`` (not GridSearchCV) — much faster on large
  feature spaces while still finding near-optimal parameters.
* Broader parameter distributions using ``scipy.stats`` distributions.
* Added grids for ``logistic_regression`` and ``gradient_boosting``.
* ``n_iter`` is configurable so callers can trade speed vs. thoroughness.
"""

from __future__ import annotations

import json
import os
import joblib

import numpy as np
from scipy.stats import loguniform, randint, uniform
from sklearn.model_selection import RandomizedSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Search spaces
# ---------------------------------------------------------------------------

PARAM_DISTRIBUTIONS: dict[str, dict] = {
    "naive_bayes": {
        "model": MultinomialNB,
        "params": {"alpha": loguniform(1e-3, 10)},
    },
    "logistic_regression": {
        "model": LogisticRegression,
        "params": {
            "C": loguniform(0.01, 100),
            "solver": ["saga", "lbfgs"],
            "max_iter": [500, 1000],
        },
    },
    "svm": {
        "model": LinearSVC,
        "params": {
            "C": loguniform(0.01, 100),
            "max_iter": [10_000],
        },
    },
    "random_forest": {
        "model": RandomForestClassifier,
        "params": {
            "n_estimators": randint(100, 500),
            "max_depth": [10, 20, 30, None],
            "min_samples_leaf": randint(1, 10),
            "max_features": ["sqrt", "log2"],
        },
    },
    "gradient_boosting": {
        "model": HistGradientBoostingClassifier,
        "params": {
            "max_iter": randint(100, 400),
            "learning_rate": loguniform(0.01, 0.3),
            "max_leaf_nodes": randint(31, 127),
            "l2_regularization": loguniform(1e-4, 1.0),
        },
    },
}

# Tree / gradient-boosting models need dense arrays
_NEEDS_DENSE: set[str] = {"random_forest", "gradient_boosting"}


def _to_dense_if_needed(X, model_name: str):
    if model_name in _NEEDS_DENSE:
        import scipy.sparse as sp
        if sp.issparse(X):
            return X.toarray()
    return X


def tune_model(
    X_train,
    y_train,
    model_name: str,
    cv: int = 5,
    n_iter: int = 20,
    random_state: int = 42,
) -> dict:
    """
    Run RandomizedSearchCV for a single model.

    Returns
    -------
    {"best_params": dict, "best_score": float, "best_model": estimator}
    """
    if model_name not in PARAM_DISTRIBUTIONS:
        raise ValueError(f"Unknown model '{model_name}'")

    cfg = PARAM_DISTRIBUTIONS[model_name]
    X = _to_dense_if_needed(X_train, model_name)

    rs = RandomizedSearchCV(
        estimator=cfg["model"](),
        param_distributions=cfg["params"],
        n_iter=n_iter,
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
        random_state=random_state,
        verbose=1,
        refit=True,
    )
    rs.fit(X, y_train)
    logger.info(
        "Tuned %s → best_score=%.4f  params=%s",
        model_name, rs.best_score_, rs.best_params_,
    )
    return {
        "best_params": rs.best_params_,
        "best_score": round(rs.best_score_, 4),
        "best_model": rs.best_estimator_,
    }


def tune_all(
    X_train,
    y_train,
    model_dir: str = "models",
    n_iter: int = 20,
) -> dict:
    """
    Tune all registered models, save optimized versions and ``best_params.json``.
    """
    all_params: dict = {}
    for name in PARAM_DISTRIBUTIONS:
        try:
            result = tune_model(X_train, y_train, name, n_iter=n_iter)
        except Exception as exc:  # pragma: no cover
            logger.warning("Skipping tuning for %s: %s", name, exc)
            continue

        all_params[name] = {
            "best_params": result["best_params"],
            "best_score": result["best_score"],
        }
        path = os.path.join(model_dir, f"optimized_{name}.pkl")
        joblib.dump(result["best_model"], path)
        logger.info("Saved optimized %s → %s", name, path)

    params_path = os.path.join(model_dir, "best_params.json")
    with open(params_path, "w") as f:
        json.dump(all_params, f, indent=2)
    logger.info("Best parameters saved → %s", params_path)
    return all_params
