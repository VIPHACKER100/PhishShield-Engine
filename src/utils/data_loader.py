"""
Data Loader — Load, validate, clean, and generate datasets.
"""

import os
import random
import pandas as pd
from src.utils.logger import logger


# ---------------------------------------------------------------------------
# Synthetic data templates
# ---------------------------------------------------------------------------
SPAM_TEMPLATES = [
    "Congratulations! You have won a ${amount} prize. Click here to claim now!",
    "URGENT: Your account has been compromised. Verify your identity immediately.",
    "FREE {item} for you! Limited time offer, act now!",
    "You are selected for a special cashback offer of {percent}%. Reply YES.",
    "Win a brand new {item}! Click the link below to enter the draw.",
    "Make money fast! Earn ${amount} per week working from home.",
    "Hot singles in your area are waiting for you. Click to meet them!",
    "Your loan of ${amount} has been pre-approved. No credit check required.",
    "Lose {amount} pounds in just {days} days with this miracle pill!",
    "CONGRATULATIONS! Claim your reward of ${amount} gift card now!",
    "Get rich quick scheme: invest ${amount} and earn ten times profit.",
    "Act now to receive exclusive discounts on {item}. Offer expires soon!",
    "You've been randomly selected to receive a free {item}. No purchase necessary.",
    "Cheap {item} available now at unbeatable prices! Order today.",
    "Secret method to earn ${amount} daily from home — guaranteed!",
    "Your email has won our international lottery worth ${amount}.",
    "Double your investment in 30 days! Risk free guaranteed returns.",
    "Buy one get one free on all {item}! This weekend only.",
    "WARNING: Your computer is infected! Download our antivirus now.",
    "Exclusive VIP membership — join today for only ${amount} per month.",
]

HAM_TEMPLATES = [
    "Hi {name}, just wanted to follow up on our meeting yesterday.",
    "Please find attached the quarterly report for your review.",
    "Reminder: team standup is at 10 AM tomorrow in the conference room.",
    "Hey {name}, are you available for a quick call this afternoon?",
    "The project deadline has been moved to next Friday. Please plan accordingly.",
    "Thanks for sending over the documents, I'll review them by end of day.",
    "Could you please share the updated spreadsheet with the latest numbers?",
    "I've completed the code review for the pull request. See my comments.",
    "Happy birthday {name}! Hope you have a wonderful day!",
    "Let's schedule a meeting to discuss the new feature requirements.",
    "The server maintenance is scheduled for this Saturday from 2-4 AM.",
    "Great job on the presentation today, {name}! Very well done.",
    "Please confirm your attendance for the company picnic next week.",
    "I'll be out of office from Monday to Wednesday. Reach out to {name} if urgent.",
    "The bug in the login module has been fixed and deployed to staging.",
    "Can we reschedule our 1-on-1 to Thursday at 3 PM?",
    "Here are the notes from today's brainstorming session.",
    "Don't forget to submit your timesheet by end of day Friday.",
    "The new hire orientation starts at 9 AM on Monday in Room 201.",
    "Thanks for your help with the client demo, it went really well!",
]

NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Quinn"]
ITEMS = ["iPhone", "laptop", "vacation", "car", "tablet", "watch", "TV", "camera"]


def _fill_template(template: str) -> str:
    """Fill a template string with random placeholder values."""
    return (
        template
        .replace("{name}", random.choice(NAMES))
        .replace("{item}", random.choice(ITEMS))
        .replace("{amount}", str(random.randint(50, 50000)))
        .replace("{percent}", str(random.randint(5, 80)))
        .replace("{days}", str(random.randint(3, 30)))
    )


def generate_sample_dataset(path: str, n: int = 1000) -> pd.DataFrame:
    """
    Generate a synthetic email dataset with *n* rows (50 / 50 spam / ham).
    Saves to *path* and returns the DataFrame.
    """
    rows = []
    for _ in range(n // 2):
        rows.append({"text": _fill_template(random.choice(SPAM_TEMPLATES)), "label": "spam"})
        rows.append({"text": _fill_template(random.choice(HAM_TEMPLATES)), "label": "ham"})
    random.shuffle(rows)
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Generated synthetic dataset with %d rows → %s", len(df), path)
    return df


def load_dataset(path: str) -> pd.DataFrame:
    """
    Load a CSV dataset and validate that it contains the required columns.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")
    df = pd.read_csv(path)
    for col in ("text", "label"):
        if col not in df.columns:
            raise ValueError(f"Dataset missing required column: '{col}'")
    logger.info("Loaded dataset with %d rows from %s", len(df), path)
    return df


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove null text rows and normalise labels to 'spam' / 'ham'.
    """
    before = len(df)
    df = df.dropna(subset=["text"]).copy()
    df["label"] = df["label"].str.strip().str.lower()
    df = df[df["label"].isin(["spam", "ham"])]
    logger.info("Cleaned dataset: %d → %d rows", before, len(df))
    return df
