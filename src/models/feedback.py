"""
Feedback — Collect user corrections and manage feedback data for retraining.
"""

import csv
import os
import sqlite3
from datetime import datetime, timezone
from src.utils.logger import logger

FEEDBACK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "feedback")
FEEDBACK_PATH = os.path.join(FEEDBACK_DIR, "feedback_data.csv")
FEEDBACK_DB = os.path.join(os.path.dirname(__file__), "..", "..", "data", "feedback.db")
FIELDS = ["timestamp", "email_text", "predicted_label", "correct_label", "model_used"]


def _ensure_file():
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    if not os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def _ensure_db():
    """Initialize SQLite database for feedback (used by retrain scheduler)."""
    os.makedirs(os.path.dirname(FEEDBACK_DB), exist_ok=True)
    conn = sqlite3.connect(FEEDBACK_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            email_text TEXT NOT NULL,
            predicted_label TEXT NOT NULL,
            correct_label TEXT NOT NULL,
            model_used TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_feedback(
    email_text: str,
    predicted_label: str,
    correct_label: str,
    model_used: str = "unknown",
) -> dict:
    """
    Record a user feedback correction.

    Parameters
    ----------
    email_text : str
        The original email text.
    predicted_label : str
        What the model predicted.
    correct_label : str
        What the user says is correct.
    model_used : str
        Which model made the prediction.

    Returns
    -------
    dict of the recorded entry.
    """
    _ensure_file()
    _ensure_db()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "email_text": email_text,
        "predicted_label": predicted_label,
        "correct_label": correct_label,
        "model_used": model_used,
    }
    # Write to CSV (for web UI / direct access)
    with open(FEEDBACK_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(entry)
    # Write to SQLite (for retrain scheduler / adaptive learning)
    conn = sqlite3.connect(FEEDBACK_DB)
    conn.execute(
        "INSERT INTO feedback (timestamp, email_text, predicted_label, correct_label, model_used) VALUES (?, ?, ?, ?, ?)",
        (entry["timestamp"], entry["email_text"], entry["predicted_label"], entry["correct_label"], entry["model_used"]),
    )
    conn.commit()
    conn.close()
    logger.info("Feedback recorded: predicted=%s, correct=%s", predicted_label, correct_label)
    return entry


def load_feedback():
    """Load all feedback entries as a list of dicts."""
    _ensure_file()
    import pandas as pd
    df = pd.read_csv(FEEDBACK_PATH)
    logger.info("Loaded %d feedback entries", len(df))
    return df


def feedback_count() -> int:
    """Return the number of feedback entries."""
    _ensure_file()
    with open(FEEDBACK_PATH, encoding="utf-8") as f:
        return sum(1 for _ in f) - 1  # minus header


def merge_feedback_into_dataset(original_csv: str, output_csv: str) -> str:
    """
    Merge feedback corrections into a training dataset.
    Uses feedback's correct_label as the ground truth.
    """
    import pandas as pd
    _ensure_file()

    original = pd.read_csv(original_csv)
    feedback = pd.read_csv(FEEDBACK_PATH)
    if feedback.empty:
        logger.info("No feedback to merge")
        return original_csv

    new_rows = feedback[["email_text", "correct_label"]].rename(
        columns={"email_text": "text", "correct_label": "label"}
    )
    merged = pd.concat([original, new_rows], ignore_index=True)
    merged.to_csv(output_csv, index=False)
    logger.info("Merged %d feedback rows into dataset → %s (%d total)", len(new_rows), output_csv, len(merged))
    return output_csv
