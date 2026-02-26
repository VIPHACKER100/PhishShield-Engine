"""
Ensemble — Voting Classifier combining NB + SVM + Decision Tree.
"""

import os
import joblib
from sklearn.ensemble import VotingClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.calibration import CalibratedClassifierCV
from src.utils.logger import logger


def build_ensemble():
    """
    Build a soft-voting ensemble.

    LinearSVC doesn't support predict_proba natively, so we wrap it
    with CalibratedClassifierCV.
    """
    estimators = [
        ("naive_bayes", MultinomialNB()),
        ("svm", CalibratedClassifierCV(LinearSVC(max_iter=10000))),
        ("decision_tree", DecisionTreeClassifier(random_state=42)),
    ]
    return VotingClassifier(estimators=estimators, voting="soft")


def train_ensemble(X_train, y_train, model_dir: str = "models"):
    """Train and save the ensemble model."""
    ensemble = build_ensemble()
    ensemble.fit(X_train, y_train)
    path = os.path.join(model_dir, "ensemble_model.pkl")
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(ensemble, path)
    logger.info("Trained and saved ensemble model → %s", path)
    return ensemble
