"""
Hyperparameter Tuning — GridSearchCV for all models.
"""

import json
import os
import joblib
from sklearn.model_selection import GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from src.utils.logger import logger

PARAM_GRIDS = {
    "naive_bayes": {
        "model": MultinomialNB,
        "params": {"alpha": [0.01, 0.1, 0.5, 1.0, 2.0]},
    },
    "svm": {
        "model": LinearSVC,
        "params": {"C": [0.01, 0.1, 1, 10], "max_iter": [10000]},
    },
    "decision_tree": {
        "model": DecisionTreeClassifier,
        "params": {
            "max_depth": [5, 10, 20, None],
            "min_samples_split": [2, 5, 10],
        },
    },
}


def tune_model(X_train, y_train, model_name: str, cv: int = 5) -> dict:
    """
    Run GridSearchCV for a single model.

    Returns
    -------
    {"best_params": dict, "best_score": float, "best_model": estimator}
    """
    if model_name not in PARAM_GRIDS:
        raise ValueError(f"Unknown model '{model_name}'")

    cfg = PARAM_GRIDS[model_name]
    gs = GridSearchCV(
        estimator=cfg["model"](),
        param_grid=cfg["params"],
        cv=cv,
        scoring="f1_macro",
        n_jobs=-1,
    )
    gs.fit(X_train, y_train)
    logger.info(
        "Tuned %s → best_score=%.4f  params=%s",
        model_name, gs.best_score_, gs.best_params_,
    )
    return {
        "best_params": gs.best_params_,
        "best_score": round(gs.best_score_, 4),
        "best_model": gs.best_estimator_,
    }


def tune_all(X_train, y_train, model_dir: str = "models") -> dict:
    """
    Tune all models, save optimized versions and best_params.json.
    """
    all_params = {}
    for name in PARAM_GRIDS:
        result = tune_model(X_train, y_train, name)
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
