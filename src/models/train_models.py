"""
Train Models — Train Naive Bayes, SVM, and Decision Tree classifiers.
"""

import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from src.utils.logger import logger

MODEL_REGISTRY = {
    "naive_bayes": MultinomialNB,
    "svm": LinearSVC,
    "decision_tree": DecisionTreeClassifier,
}

DEFAULT_PARAMS = {
    "naive_bayes": {},
    "svm": {"max_iter": 10000},
    "decision_tree": {"random_state": 42},
}


def split_data(X, y, test_size: float = 0.2, random_state: int = 42):
    """80/20 train-test split."""
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def train_model(X_train, y_train, model_name: str, params: dict | None = None):
    """
    Train a single model by name.

    Parameters
    ----------
    model_name : str
        One of "naive_bayes", "svm", "decision_tree".
    params : dict, optional
        Override default parameters.
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{model_name}'. Choose from {list(MODEL_REGISTRY)}")

    final_params = {**DEFAULT_PARAMS.get(model_name, {}), **(params or {})}
    model = MODEL_REGISTRY[model_name](**final_params)
    model.fit(X_train, y_train)
    logger.info("Trained %s model", model_name)
    return model


def save_model(model, path: str):
    """Persist a trained model."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logger.info("Saved model → %s", path)


def load_model(path: str):
    """Load a persisted model."""
    model = joblib.load(path)
    logger.info("Loaded model from %s", path)
    return model


def train_all(X_train, y_train, model_dir: str = "models"):
    """
    Train all registered models and save them.
    Returns dict of {model_name: model}.
    """
    trained = {}
    for name in MODEL_REGISTRY:
        model = train_model(X_train, y_train, name)
        save_model(model, os.path.join(model_dir, f"{name}.pkl"))
        trained[name] = model
    return trained
