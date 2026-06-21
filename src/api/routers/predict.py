import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from arq import create_pool
from arq.connections import RedisSettings

from src.api.schemas import PredictRequest, BatchPredictRequest, FeedbackRequest
from src.api.dependencies import ab_test, optional_auth
from src.models.predict import predict_email, predict_batch
from src.models.feedback import save_feedback, feedback_count
from src.utils.logger import logger
from src.utils.anonymizer import anonymize_text

router = APIRouter(tags=["predict"])

# ---------------------------------------------------------------------------
# ARQ pool (lazy-initialized)
# ---------------------------------------------------------------------------

_arq_pool = None

async def _get_arq_pool():
    """Lazily create and cache the ARQ Redis connection pool."""
    global _arq_pool
    if _arq_pool is None:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        try:
            _arq_pool = await create_pool(RedisSettings(host=redis_host, port=6379))
        except Exception as e:
            logger.warning("ARQ pool unavailable (Redis not running?): %s. Falling back to sync.", e)
    return _arq_pool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/predict")
async def predict(request: PredictRequest):
    try:
        model_name = request.model
        if model_name is None:
            model_name = ab_test.select()

        result = predict_email(request.text, model_name, request.headers or "")
        logger.info("Email prediction: %s", result['prediction'])

        # Enqueue background tasks via ARQ (falls back to sync if Redis unavailable)
        pool = await _get_arq_pool()
        if pool:
            await pool.enqueue_job("check_drift", request.text, result['prediction'])
            if result.get("security_risk_score", 0) >= 75:
                await pool.enqueue_job("send_security_alert", "Phishing Detection", result)
        else:
            # Sync fallback when Redis is not available (e.g., local dev)
            from src.models.drift_monitor import DriftMonitor
            DriftMonitor().check([request.text], [result['prediction']])

        return result
    except Exception as e:
        logger.error("Prediction error: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-security")
async def analyze_security_endpoint(body: PredictRequest):
    from src.security.risk_scoring import calculate_security_risk
    try:
        analysis = calculate_security_risk(body.text, body.headers or "")
        return analysis
    except Exception as e:
        logger.error("Security analysis error: %s", e)
        raise HTTPException(status_code=500, detail="Security scanning failed")

@router.post("/predict/batch")
async def predict_batch_endpoint(body: BatchPredictRequest, request: Request, user: str = Depends(optional_auth)):
    try:
        results = predict_batch(body.emails, body.model_name)
        return {"results": results, "count": len(results)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Batch prediction error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal prediction error")

@router.post("/export-report")
async def export_report_endpoint(body: PredictRequest):
    from src.security.risk_scoring import calculate_security_risk
    from src.security.url_extractor import extract_urls
    try:
        analysis = calculate_security_risk(body.text, body.headers or "")
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_email": body.text,
            "extracted_urls": extract_urls(body.text),
            "forensic_analysis": analysis
        }
        return JSONResponse(content=report)
    except Exception as e:
        logger.error("Export report error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate report")

@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest):
    clean_text = anonymize_text(body.email_text)
    entry = save_feedback(
        email_text=clean_text,
        predicted_label=body.predicted_label,
        correct_label=body.correct_label,
        model_used=body.model_used,
    )
    ab_test.record(body.model_used, body.predicted_label, body.correct_label)
    ab_test.save()
    return {"status": "recorded", "feedback_total": feedback_count(), "entry": entry}
