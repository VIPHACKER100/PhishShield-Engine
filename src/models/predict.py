"""
Predict — Inference pipeline for email classification.

Combines traditional ML (TF-IDF + sklearn), deep learning (Transformers),
vector similarity search (ChromaDB), and deterministic security heuristics.
"""

import os
import json
import joblib
from src.preprocessing.text_cleaner import preprocess_text
from src.utils.logger import logger
from src.models.deep_learning import DeepLearningModel
from src.models.vector_search import VectorSearchDB

import functools

# ---------------------------------------------------------------------------
# Lazy-loaded singletons for heavy ML resources
# ---------------------------------------------------------------------------

_dl_model: DeepLearningModel | None = None
_vector_db: VectorSearchDB | None = None


def _get_dl_model() -> DeepLearningModel:
    """Lazy-load the transformer model once."""
    global _dl_model
    if _dl_model is None:
        _dl_model = DeepLearningModel()
        _dl_model.load()
    return _dl_model


def _get_vector_db() -> VectorSearchDB:
    """Lazy-load the ChromaDB vector store once."""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorSearchDB()
        _vector_db.initialize()
    return _vector_db

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

    Ensemble pipeline:
      1. Deterministic security heuristics (SPF, DKIM, homographs, etc.)
      2. Traditional ML (TF-IDF + sklearn model)
      3. Deep learning (HuggingFace Transformer)
      4. Vector similarity search (ChromaDB)
      5. SHAP explainability
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

    # 2. Run Traditional ML Model (TF-IDF + sklearn)
    vectorizer = _load_vectorizer(vectorizer_path)
    model = _load_model(model_path)

    cleaned = preprocess_text(text)
    features = vectorizer.transform([cleaned])

    ml_prediction = model.predict(features)[0]

    # Confidence (probability)
    ml_confidence = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(features)[0]
        ml_confidence = float(max(proba))
    elif hasattr(model, "decision_function"):
        import numpy as np
        df = model.decision_function(features)[0]
        ml_confidence = float(1.0 / (1.0 + np.exp(-abs(df))))

    # 3. Run Deep Learning Model (Transformer)
    dl_result = {"prediction": None, "confidence": None, "model_used": None}
    try:
        dl_model = _get_dl_model()
        dl_result = dl_model.predict(text)
    except Exception as e:
        logger.warning("Deep learning model unavailable, falling back to ML-only: %s", e)

    # 4. Run Vector Similarity Search
    similar_threats = []
    try:
        vector_db = _get_vector_db()
        similar_threats = vector_db.search_similar(text, n_results=3)
    except Exception as e:
        logger.warning("Vector search unavailable: %s", e)

    # 5. Ensemble decision
    # Priority: security override > DL confidence > ML confidence > vector similarity
    final_prediction = ml_prediction

    # If the deep learning model has a strong opinion, let it weigh in
    if dl_result["prediction"] is not None:
        dl_conf = dl_result.get("confidence", 0) or 0
        ml_conf = ml_confidence or 0
        # If DL says spam with high confidence, trust it
        if dl_result["prediction"] == "spam" and dl_conf > 0.7:
            final_prediction = "spam"
        # If ML and DL disagree, trust the more confident one
        elif dl_result["prediction"] != ml_prediction and dl_conf > ml_conf:
            final_prediction = dl_result["prediction"]

    # Vector similarity boost: if similar known phishing emails found
    if similar_threats:
        spam_matches = sum(1 for m in similar_threats
                          if m.get("metadata", {}).get("label") == "spam"
                          and m.get("distance", 999) < 0.5)
        if spam_matches >= 2:
            final_prediction = "spam"
            logger.info("Vector similarity override: %d close phishing matches found", spam_matches)

    # Security rule override (highest priority)
    if security_analysis["risk_score"] > 80:
        final_prediction = "spam"
        logger.info("Security Rule Override: Flagging as SPAM due to high risk score (%d)",
                    security_analysis["risk_score"])

    # 6. Explainability (SHAP with model + vectorizer passed in)
    from src.models.explainability import get_prediction_explanation
    explanation = get_prediction_explanation(
        text, final_prediction, security_analysis,
        model=model, vectorizer=vectorizer
    )

    result = {
        "email_text": text,
        "prediction": final_prediction,
        "ml_prediction": ml_prediction,
        "ml_confidence": round(float(ml_confidence), 3) if ml_confidence else None,
        "dl_prediction": dl_result.get("prediction"),
        "dl_confidence": dl_result.get("confidence"),
        "dl_model": dl_result.get("model_used"),
        "similar_threats": [
            {"distance": m["distance"], "label": m["metadata"].get("label")}
            for m in similar_threats
        ],
        "model_used": model_name,
        "security_risk_score": security_analysis["risk_score"],
        "security_risk_level": security_analysis["risk_level"],
        "security_flags": security_analysis["security_flags"],
        "threat_reasons": security_analysis["threat_reasons"],
        "threat_explanation": explanation["summary"],
        "shap_analysis": explanation.get("shap_analysis", []),
        "security_details": security_analysis["details"]
    }

    logger.info("Prediction: %s (risk=%d, ml=%s, dl=%s, model=%s)",
                final_prediction, security_analysis["risk_score"],
                ml_prediction, dl_result.get("prediction"), model_name)
    return result


def predict_batch(texts: list[str], model_name: str | None = None) -> list[dict]:
    """Classify multiple emails."""
    return [predict_email(t, model_name) for t in texts]
