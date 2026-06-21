"""
Explainability Layer — Provide reasoning and feature importance for predictions using SHAP.
"""
import shap
import numpy as np
from src.preprocessing.text_cleaner import preprocess_text

def get_prediction_explanation(text: str, prediction: str, security_results: dict, model=None, vectorizer=None) -> dict:
    """
    Generate a human-readable explanation and SHAP feature importances.
    """
    clean_text = preprocess_text(text)
    
    # 1. Extract security logic (Deterministic rules)
    sec_reasons = security_results.get("threat_reasons", [])
    risk_level = security_results.get("risk_level", "LOW")
    
    shap_keywords = []
    
    # 2. Extract ML Feature Importance (SHAP)
    # This requires the trained scikit-learn pipeline (vectorizer + model)
    if model and vectorizer:
        try:
            # We use an Explainer tailored for text/linear models
            # In production, SHAP explainers should be initialized once and cached
            explainer = shap.LinearExplainer(model, vectorizer.transform([""]))
            vec_text = vectorizer.transform([clean_text])
            shap_values = explainer.shap_values(vec_text)
            
            # Get feature names from vectorizer
            feature_names = np.array(vectorizer.get_feature_names_out())
            
            # Get top contributing words
            if isinstance(shap_values, list):
                # For multi-class (or some binary configs), grab the positive class
                vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            else:
                vals = shap_values[0]
                
            # Sort by absolute impact
            top_indices = np.argsort(-np.abs(vals))[:5]
            for idx in top_indices:
                if vals[idx] != 0:
                    shap_keywords.append({
                        "word": feature_names[idx],
                        "impact": round(vals[idx], 4)
                    })
        except Exception as e:
            # Fallback if SHAP fails or model is incompatible
            pass

    # 3. Construct summary
    if prediction == "spam":
        summary = "Classified as SPAM. "
        factors = []
        if sec_reasons:
            factors.append(f"Detected {len(sec_reasons)} security threats.")
        if shap_keywords:
            top_words = [kw["word"] for kw in shap_keywords if kw["impact"] > 0][:3]
            if top_words:
                factors.append(f"Suspicious semantic patterns identified around: {', '.join(top_words)}.")
        
        if not factors:
            summary += "Based on deep model confidence patterns."
        else:
            summary += " ".join(factors)
    else:
        summary = "Classified as HAM (Safe). No significant threats detected."

    return {
        "summary": summary,
        "risk_level": risk_level,
        "shap_analysis": shap_keywords,
        "security_threats": sec_reasons
    }
