"""
Drift Monitor — Detect distribution shifts between training and live data.
"""

import json
import os
import numpy as np
from collections import Counter
from src.utils.logger import logger

DRIFT_LOG = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "drift_log.json")


class DriftMonitor:
    """
    Monitor prediction distribution, input length, and vocabulary drift.

    Usage
    -----
    monitor = DriftMonitor(training_stats)
    alert = monitor.check(live_predictions, live_texts)
    """

    def __init__(self, training_stats: dict | None = None):
        """
        Parameters
        ----------
        training_stats : dict
            Pre-computed stats from training data. Keys:
            - spam_ratio: float (fraction of spam in training)
            - avg_text_length: float
            - vocab: set or list of frequent training words
        """
        self.training_stats = training_stats or {}
        self.threshold_spam_ratio = 0.15    # alert if ratio shifts > 15%
        self.threshold_length_pct = 0.30    # alert if avg length shifts > 30%
        self.threshold_vocab_drift = 0.40   # alert if >40% new words

    def compute_training_stats(self, labels: list[str], texts: list[str]) -> dict:
        """Compute and store baseline statistics from training data."""
        spam_count = sum(1 for l in labels if l == "spam")
        self.training_stats = {
            "spam_ratio": spam_count / len(labels) if labels else 0,
            "avg_text_length": np.mean([len(t) for t in texts]) if texts else 0,
            "vocab": list(set(" ".join(texts).split()))[:5000],  # top 5k unique words
            "total_samples": len(labels),
        }
        logger.info("Computed training stats: spam_ratio=%.3f, avg_len=%.1f, vocab_size=%d",
                     self.training_stats["spam_ratio"],
                     self.training_stats["avg_text_length"],
                     len(self.training_stats["vocab"]))
        return self.training_stats

    def check(self, predictions: list[str], texts: list[str]) -> dict:
        """
        Check live data against training baseline.

        Returns
        -------
        dict with alert flags and details.
        """
        if not self.training_stats:
            return {"error": "No training stats available. Call compute_training_stats first."}

        alerts = []

        # 1. Prediction distribution drift
        live_spam_ratio = sum(1 for p in predictions if p == "spam") / len(predictions) if predictions else 0
        train_spam_ratio = self.training_stats.get("spam_ratio", 0.5)
        ratio_diff = abs(live_spam_ratio - train_spam_ratio)
        if ratio_diff > self.threshold_spam_ratio:
            alerts.append({
                "type": "prediction_distribution",
                "message": f"Spam ratio shifted: train={train_spam_ratio:.3f} → live={live_spam_ratio:.3f} (Δ={ratio_diff:.3f})",
                "severity": "warning" if ratio_diff < 0.3 else "critical",
            })

        # 2. Input length drift
        live_avg_len = np.mean([len(t) for t in texts]) if texts else 0
        train_avg_len = self.training_stats.get("avg_text_length", 1)
        len_shift = abs(live_avg_len - train_avg_len) / train_avg_len if train_avg_len else 0
        if len_shift > self.threshold_length_pct:
            alerts.append({
                "type": "input_length",
                "message": f"Avg text length shifted: train={train_avg_len:.0f} → live={live_avg_len:.0f} ({len_shift:.0%})",
                "severity": "warning",
            })

        # 3. Vocabulary drift
        train_vocab = set(self.training_stats.get("vocab", []))
        live_words = set(" ".join(texts).split())
        if train_vocab and live_words:
            new_words = live_words - train_vocab
            drift_ratio = len(new_words) / len(live_words) if live_words else 0
            if drift_ratio > self.threshold_vocab_drift:
                alerts.append({
                    "type": "vocabulary_drift",
                    "message": f"{drift_ratio:.0%} of live words not in training vocabulary ({len(new_words)} new words)",
                    "severity": "warning",
                })

        result = {
            "has_drift": len(alerts) > 0,
            "alerts": alerts,
            "live_stats": {
                "spam_ratio": round(live_spam_ratio, 4),
                "avg_text_length": round(live_avg_len, 1),
                "num_predictions": len(predictions),
            },
        }

        # Log
        self._log_check(result)
        if alerts:
            for a in alerts:
                logger.warning("DRIFT ALERT [%s]: %s", a["severity"].upper(), a["message"])
        else:
            logger.info("No drift detected (%d predictions checked)", len(predictions))

        return result

    def _log_check(self, result: dict):
        os.makedirs(os.path.dirname(DRIFT_LOG), exist_ok=True)
        from datetime import datetime, timezone
        logs = []
        if os.path.exists(DRIFT_LOG):
            with open(DRIFT_LOG) as f:
                logs = json.load(f)
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        logs.append(result)
        with open(DRIFT_LOG, "w") as f:
            json.dump(logs, f, indent=2)
