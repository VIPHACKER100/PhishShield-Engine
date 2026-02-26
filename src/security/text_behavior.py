"""
Behavioral Text Analysis — Identify psychological triggers and writing patterns used in phishing.
"""

import re

URGENCY_WORDS = {
    "urgent", "action required", "suspended", "immediately", "act now", 
    "locked", "security alert", "unauthorized", "expired", "final notice"
}

REWARD_WORDS = {
    "winner", "prize", "gift card", "reward", "lottery", "cash", 
    "congratulations", "won", "free", "discount"
}

def analyze_text_behavior(text: str) -> dict:
    """
    Extract behavioral and psychological signals from email text.
    """
    if not text:
        return {"behavior_score": 0}

    low_text = text.lower()
    
    # 1. Count triggers
    urgency_matches = [w for w in URGENCY_WORDS if w in low_text]
    reward_matches = [w for w in REWARD_WORDS if w in low_text]
    
    # 2. Structural signals
    exclamation_count = text.count('!')
    caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
    
    # 3. Decision scores
    behavior_score = 0
    behavior_score += len(urgency_matches) * 15
    behavior_score += len(reward_matches) * 10
    behavior_score += min(exclamation_count * 5, 20)
    if caps_ratio > 0.3: behavior_score += 20

    return {
        "behavior_score": min(behavior_score, 100),
        "urgency_triggers": urgency_matches,
        "reward_triggers": reward_matches,
        "is_urgent": len(urgency_matches) > 0,
        "is_reward_bait": len(reward_matches) > 0,
        "high_caps_flag": caps_ratio > 0.3,
        "exclamation_excess": exclamation_count > 3
    }
