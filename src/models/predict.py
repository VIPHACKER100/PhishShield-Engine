"""
Predict — Inference pipeline for email classification.
"""

import os
import json
import joblib
from src.preprocessing.text_cleaner import preprocess_text
from src.utils.logger import logger

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models")


def _default_model_name() -> str:
    """Return the best model name from metrics.json, or fallback to naive_bayes."""
    metrics_path = os.path.join(_BASE, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            return json.load(f).get("best_model", "naive_bayes")
    return "naive_bayes"


def predict_email(text: str, model_name: str | None = None, raw_headers: str = "") -> dict:
    """
    Classify a single email text with security scanning.
    """
    from src.security.risk_scoring import calculate_security_risk, run_security_rules

    if model_name is None:
        model_name = _default_model_name()

    vectorizer_path = os.path.join(_BASE, "vectorizer.pkl")
    model_path = os.path.join(_BASE, f"{model_name}.pkl")

    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError("Vectorizer not found. Run training first.")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model '{model_name}' not found at {model_path}")

    # 1. Run Security Analysis with optional headers
    security_analysis = calculate_security_risk(text, raw_headers)
    
    # 2. Run ML Model
    vectorizer = joblib.load(vectorizer_path)
    model = joblib.load(model_path)

    cleaned = preprocess_text(text)
    features = vectorizer.transform([cleaned])
    
    prediction = model.predict(features)[0]

    # Confidence (probability)
    confidence = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(features)[0]
        confidence = max(proba)

    # Rule-based override (Phase 45)
    final_prediction = prediction
    if security_analysis["risk_score"] > 80:
        final_prediction = "spam"
        logger.info("Security Rule Override: Flagging as SPAM due to high risk score (%d)", 
                    security_analysis["risk_score"])
        
    # Explainability (Phase 58)
    from src.models.explainability import get_prediction_explanation
    explanation = get_prediction_explanation(text, final_prediction, security_analysis)

    result = {
        "email_text": text,
        "prediction": final_prediction,
        "ml_prediction": prediction,
        "confidence": round(float(confidence), 3) if confidence else None,
        "model_used": model_name,
        "security_risk_score": security_analysis["risk_score"],
        "security_risk_level": security_analysis["risk_level"],
        "security_flags": security_analysis["security_flags"],
        "threat_reasons": security_analysis["threat_reasons"],
        "threat_explanation": explanation["summary"],
        "security_details": security_analysis["details"]
    }
    
    logger.info("Prediction: %s (risk=%d, model=%s)", 
                final_prediction, security_analysis["risk_score"], model_name)
    return result


def predict_batch(texts: list[str], model_name: str | None = None) -> list[dict]:
    """Classify multiple emails."""
    return [predict_email(t, model_name) for t in texts]
