"""
A/B Testing — Route traffic between models and track outcomes.
"""

import json
import os
import random
from datetime import datetime, timezone
from src.utils.logger import logger

AB_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "ab_test_results.json")


class ABTest:
    """
    Simple A/B test router with configurable traffic split.

    Usage
    -----
    ab = ABTest("naive_bayes", "ensemble_model", split=0.8)
    model_name = ab.select()        # 80% → model A, 20% → model B
    ab.record(model_name, result)   # log outcome
    """

    def __init__(self, model_a: str, model_b: str, split: float = 0.8):
        self.model_a = model_a
        self.model_b = model_b
        self.split = split  # fraction of traffic going to model_a
        self._results: list[dict] = []

    def select(self) -> str:
        """Randomly select a model based on the traffic split."""
        return self.model_a if random.random() < self.split else self.model_b

    def record(self, model_used: str, prediction: str, correct_label: str | None = None):
        """Record an A/B test outcome."""
        entry = {
            "model": model_used,
            "prediction": prediction,
            "correct_label": correct_label,
            "is_correct": prediction == correct_label if correct_label else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._results.append(entry)
        return entry

    def save(self, path: str = AB_LOG_PATH):
        """Persist results to JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = []
        if os.path.exists(path):
            with open(path) as f:
                existing = json.load(f)
        existing.extend(self._results)
        with open(path, "w") as f:
            json.dump(existing, f, indent=2)
        logger.info("Saved %d A/B test results → %s", len(self._results), path)
        self._results.clear()

    def summary(self) -> dict:
        """Return win-rate summary for each model."""
        path = AB_LOG_PATH
        if not os.path.exists(path):
            return {"error": "No A/B test data available"}
        with open(path) as f:
            data = json.load(f)
        summary = {}
        for entry in data:
            m = entry["model"]
            if m not in summary:
                summary[m] = {"total": 0, "correct": 0}
            summary[m]["total"] += 1
            if entry.get("is_correct"):
                summary[m]["correct"] += 1
        for m, s in summary.items():
            s["accuracy"] = round(s["correct"] / s["total"], 4) if s["total"] else 0
        return summary
