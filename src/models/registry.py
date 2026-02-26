"""
Model Registry — Track trained models, their lifecycle, and metadata.
"""

import json
import os
from datetime import datetime, timezone
from src.utils.logger import logger

REGISTRY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "registry")
REGISTRY_PATH = os.path.join(REGISTRY_DIR, "registry.json")


def _load_registry() -> list[dict]:
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return []


def _save_registry(entries: list[dict]):
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def register_model(
    model_name: str,
    algorithm: str,
    file_path: str,
    metrics: dict,
    dataset_version: str = "unknown",
    parameters: dict | None = None,
    status: str = "active",
) -> dict:
    """
    Add a model to the registry.

    Parameters
    ----------
    model_name : str
        Display name / identifier.
    algorithm : str
        Algorithm type (e.g. "MultinomialNB").
    file_path : str
        Path to .pkl file.
    metrics : dict
        Evaluation metrics (accuracy, f1, etc.).
    dataset_version : str
        Which dataset version was used for training.
    parameters : dict
        Hyperparameters used.
    status : str
        "active" or "archived".
    """
    entries = _load_registry()
    version = sum(1 for e in entries if e["model_name"] == model_name) + 1
    entry = {
        "model_name": model_name,
        "version": version,
        "algorithm": algorithm,
        "dataset_version": dataset_version,
        "parameters": parameters or {},
        "metrics": metrics,
        "file_path": file_path,
        "status": status,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    _save_registry(entries)
    logger.info("Registered model '%s' v%d (status=%s)", model_name, version, status)
    return entry


def list_models(status: str | None = None) -> list[dict]:
    """List all registered models, optionally filtered by status."""
    entries = _load_registry()
    if status:
        entries = [e for e in entries if e["status"] == status]
    return entries


def get_active_model(model_name: str) -> dict | None:
    """Get the latest active version of a model."""
    entries = _load_registry()
    candidates = [e for e in entries if e["model_name"] == model_name and e["status"] == "active"]
    return max(candidates, key=lambda e: e["version"]) if candidates else None


def archive_model(model_name: str, version: int):
    """Archive a specific model version."""
    entries = _load_registry()
    for e in entries:
        if e["model_name"] == model_name and e["version"] == version:
            e["status"] = "archived"
            logger.info("Archived %s v%d", model_name, version)
    _save_registry(entries)


def get_best_model() -> dict | None:
    """Return the active model with the highest F1 score."""
    entries = [e for e in _load_registry() if e["status"] == "active" and "f1_score" in e.get("metrics", {})]
    return max(entries, key=lambda e: e["metrics"]["f1_score"]) if entries else None
