"""
Explainability Layer — Provide reasoning and feature importance for predictions.
"""

from src.preprocessing.text_cleaner import preprocess_text

# High-impact spam keywords from training context
SPAM_KWS = {"free", "win", "prize", "cash", "account", "verify", "urgent", "offer", "click"}

def get_prediction_explanation(text: str, prediction: str, security_results: dict) -> dict:
    """
    Generate a human-readable explanation for why an email was classified.
    """
    clean_text = preprocess_text(text)
    words = clean_text.split()
    
    # 1. Identify suspicious words
    triggers = [w for w in set(words) if w in SPAM_KWS]
    
    # 2. Extract security logic
    sec_reasons = security_results.get("threat_reasons", [])
    risk_level = security_results.get("risk_level", "LOW")
    
    # 3. Construct summary
    if prediction == "spam":
        summary = "Classified as SPAM due to "
        factors = []
        if sec_reasons:
            factors.append(f"{len(sec_reasons)} security threats")
        if triggers:
            factors.append(f"suspicious keywords: {', '.join(triggers[:3])}")
        
        if not factors:
            summary += "model confidence patterns."
        else:
            summary += " and ".join(factors) + "."
    else:
        summary = "Classified as HAM (Safe). No significant threats or spam patterns detected."

    return {
        "summary": summary,
        "risk_level": risk_level,
        "top_keywords": triggers,
        "security_threats": sec_reasons
    }
