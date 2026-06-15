"""
Predict — Inference pipeline for email classification.
"""

import os
import json
import joblib
from src.preprocessing.text_cleaner import preprocess_text
from src.utils.logger import logger

import functools

@functools.lru_cache(maxsize=1)
def _load_vectorizer(path: str):
    return joblib.load(path)

@functools.lru_cache(maxsize=5)
def _load_model(path: str):
    return joblib.load(path)

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models")


def _allowed_model_names() -> set[str]:
    """Return the set of allowed model names derived from local model files."""
    allowed = set()
    if os.path.isdir(_BASE):
        for filename in os.listdir(_BASE):
            if filename.endswith(".pkl") and filename != "vectorizer.pkl":
                allowed.add(filename[:-4])
    return allowed


def _sanitize_model_name(model_name: str | None) -> str:
    """
    Ensure model_name is restricted to known local model artifacts.
    Return a canonical trusted value sourced from the local allowlist.
    """
    candidate = _default_model_name() if model_name is None else model_name
    allowed = _allowed_model_names()
    if candidate not in allowed:
        raise ValueError(f"Unsupported model '{candidate}'. Allowed models: {sorted(allowed)}")
    return next(name for name in allowed if name == candidate)


def _safe_model_path(model_name: str) -> str:
    """
    Build a model path and ensure it remains under the models base directory.
    """
    base_abs = os.path.abspath(_BASE)
    model_path = os.path.abspath(os.path.join(_BASE, f"{model_name}.pkl"))
    if os.path.commonpath([base_abs, model_path]) != base_abs:
        raise ValueError("Invalid model path")
    return model_path


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
    from src.security.risk_scoring import calculate_security_risk

    model_name = _sanitize_model_name(model_name)

    vectorizer_path = os.path.join(_BASE, "vectorizer.pkl")
    model_path = _safe_model_path(model_name)

    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError("Vectorizer not found. Run training first.")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model '{model_name}' not found at {model_path}")

    # 1. Run Security Analysis with optional headers
    security_analysis = calculate_security_risk(text, raw_headers)
    
    # 2. Run ML Model (using cached loaders)
    vectorizer = _load_vectorizer(vectorizer_path)
    model = _load_model(model_path)

    cleaned = preprocess_text(text)
    features = vectorizer.transform([cleaned])
    
    prediction = model.predict(features)[0]

    # Confidence (probability)
    confidence = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(features)[0]
        confidence = float(max(proba))
    elif hasattr(model, "decision_function"):
        # For non-calibrated SVMs (fallback)
        import numpy as np
        df = model.decision_function(features)[0]
        confidence = float(1.0 / (1.0 + np.exp(-abs(df))))

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
