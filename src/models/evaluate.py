"""
Evaluate — Compute metrics for trained models and persist results.
"""

import json
import os
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from src.utils.logger import logger


def evaluate_model(model, X_test, y_test, model_name: str) -> dict:
    """
    Evaluate a single model and return a metrics dictionary.
    """
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred).tolist()
    metrics = {
        "model": model_name,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, pos_label="spam", zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, pos_label="spam", zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, pos_label="spam", zero_division=0), 4),
        "confusion_matrix": cm,
    }
    logger.info(
        "%s → acc=%.4f  prec=%.4f  rec=%.4f  f1=%.4f",
        model_name, metrics["accuracy"], metrics["precision"],
        metrics["recall"], metrics["f1_score"],
    )
    return metrics


def evaluate_all(models: dict, X_test, y_test, output_path: str = "models/metrics.json") -> dict:
    """
    Evaluate all models and save results.

    Parameters
    ----------
    models : dict
        {model_name: fitted_model}

    Returns
    -------
    dict with 'results' list and 'best_model' name.
    """
    results = []
    for name, model in models.items():
        results.append(evaluate_model(model, X_test, y_test, name))

    best = max(results, key=lambda r: r["f1_score"])
    report = {"results": results, "best_model": best["model"]}

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("Best model: %s (F1=%.4f). Metrics saved → %s",
                best["model"], best["f1_score"], output_path)
    return report
