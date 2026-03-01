"""
Ensemble — Upgraded stacking / voting ensemble for spam classification.

Combines the best-performing models into a:
1. Soft-VotingClassifier (fast, good default)
2. StackingClassifier with LogisticRegression meta-learner (best accuracy)

Both are trained and saved; the pipeline picks the one flagged in --ensemble.
"""

from __future__ import annotations

import os
import joblib

import scipy.sparse as sp
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MaxAbsScaler

from src.models.train_models import DenseTransformer
from src.utils.logger import logger

# ---------------------------------------------------------------------------
# Optional LightGBM
# ---------------------------------------------------------------------------
try:
    from lightgbm import LGBMClassifier
    _LGBM_AVAILABLE = True
except ImportError:
    _LGBM_AVAILABLE = False


def _base_estimators() -> list[tuple[str, object]]:
    """Return a list of (name, estimator) for use in ensembles."""
    estimators: list[tuple[str, object]] = [
        ("nb", MultinomialNB(alpha=0.1)),
        # LinearSVC needs calibration for soft voting / stacking
        ("svm", CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=10_000), cv=3)),
        # HistGB works on dense arrays; we wrap it so sparse input is handled
        (
            "hgb",
            Pipeline([
                ("scaler", MaxAbsScaler()),
                ("dense", DenseTransformer()),
                ("clf", HistGradientBoostingClassifier(
                    max_iter=200, learning_rate=0.1, max_leaf_nodes=63, random_state=42
                )),
            ]),
        ),
    ]
    if _LGBM_AVAILABLE:
        estimators.append((
            "lgbm",
            Pipeline([
                ("scaler", MaxAbsScaler()),
                ("clf", LGBMClassifier(
                    n_estimators=300, learning_rate=0.05,
                    num_leaves=63, n_jobs=-1, random_state=42, verbosity=-1,
                )),
            ])
        ))
    return estimators


def build_voting_ensemble() -> VotingClassifier:
    """Soft-voting ensemble — fast, interpretable, good baseline."""
    return VotingClassifier(
        estimators=_base_estimators(),
        voting="soft",
        n_jobs=-1,
    )


def build_stacking_ensemble() -> StackingClassifier:
    """
    Stacking ensemble with LogisticRegression meta-learner.

    Uses 5-fold cross-val to generate out-of-fold predictions as
    meta-features, then fits the meta-learner.  Typically 1-3% better than
    voting but ~3× slower to train.
    """
    return StackingClassifier(
        estimators=_base_estimators(),
        final_estimator=LogisticRegression(C=1.0, solver="lbfgs", max_iter=500),
        cv=5,
        stack_method="predict_proba",
        n_jobs=-1,
        passthrough=False,
    )


def train_ensemble(
    X_train,
    y_train,
    model_dir: str = "models",
    kind: str = "voting",   # "voting" | "stacking"
) -> object:
    """
    Train and save an ensemble model.

    Parameters
    ----------
    kind : str
        ``"voting"`` (default, fast) or ``"stacking"`` (slower, more accurate).
    """
    if kind == "stacking":
        ensemble = build_stacking_ensemble()
        filename = "ensemble_stacking.pkl"
    else:
        ensemble = build_voting_ensemble()
        filename = "ensemble_model.pkl"

    logger.info("Training %s ensemble...", kind)
    ensemble.fit(X_train, y_train)
    os.makedirs(model_dir, exist_ok=True)
    path = os.path.join(model_dir, filename)
    joblib.dump(ensemble, path)
    logger.info("Saved %s ensemble → %s", kind, path)
    return ensemble
