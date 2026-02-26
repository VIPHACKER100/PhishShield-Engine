"""
FastAPI Application — Main API server with prediction, batch, analytics,
authentication, rate limiting, and security hardening.
"""

import os
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from src.models.predict import predict_email, predict_batch
from src.models.feedback import save_feedback, feedback_count
from src.models.ab_testing import ABTest
from src.models.drift_monitor import DriftMonitor
from src.utils.anonymizer import anonymize_text
from src.api.auth import (
    register_user, authenticate_user, verify_token, verify_api_key, log_usage,
)
from src.utils.logger import logger, generate_request_id

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Email Spam Classifier API",
    description="Classify emails as Spam or Ham using ML models.",
    version="2.0.0",
)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# A/B Testing state (Simplified, in-memory toggle)
ab_test = ABTest("naive_bayes", "svm", split=0.5)
drift_monitor = DriftMonitor()

# ---------------------------------------------------------------------------
# Rate limiting (in-memory, per-IP, simple)
# ---------------------------------------------------------------------------

_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 60          # requests
RATE_WINDOW = 60         # seconds

MAX_TEXT_LENGTH = 50_000  # characters


def _check_rate_limit(ip: str):
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_WINDOW]
    if len(_rate_store[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    _rate_store[ip].append(now)


# ---------------------------------------------------------------------------
# Auth dependency (optional — only enforced if users exist)
# ---------------------------------------------------------------------------

async def optional_auth(request: Request) -> Optional[str]:
    """
    Attempt to authenticate via Bearer token or X-API-Key header.
    Returns username or None (open access when no users registered).
    """
    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("X-API-Key", "")

    if auth_header.startswith("Bearer "):
        user = verify_token(auth_header[7:])
        if user:
            return user

    if api_key:
        user = verify_api_key(api_key)
        if user:
            return user

    return None


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    model: Optional[str] = None
    headers: Optional[str] = ""

    @field_validator("text")
    @classmethod
    def sanitise(cls, v: str) -> str:
        return v.strip()


class BatchPredictRequest(BaseModel):
    emails: list[str] = Field(..., min_length=1, max_length=100)
    model_name: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class FeedbackRequest(BaseModel):
    email_text: str = Field(..., min_length=1)
    predicted_label: str
    correct_label: str
    model_used: str = "unknown"


# ---------------------------------------------------------------------------
# Middleware — request ID + rate limit
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    req_id = generate_request_id()
    request.state.request_id = req_id
    _check_rate_limit(request.client.host if request.client else "unknown")
    start = time.time()
    response = await call_next(request)
    duration = round(time.time() - start, 3)
    logger.info(
        "[%s] %s %s → %s (%.3fs)",
        req_id, request.method, request.url.path, response.status_code, duration,
        extra={"request_id": req_id},
    )
    response.headers["X-Request-ID"] = req_id
    return response


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


# ---------------------------------------------------------------------------
# Prediction endpoints
# ---------------------------------------------------------------------------

@app.post("/predict")
async def predict(request: PredictRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to classify an email as Spam or Ham.
    """
    try:
        # Use A/B testing if no specific model requested
        model_name = request.model
        if model_name is None:
            model_name = ab_test.select()

        # Run prediction
        result = predict_email(request.text, model_name, request.headers or "")
        
        # Log for monitoring
        logger.info("Email prediction: %s", result['prediction'])
        
        # Background task for drift monitoring (Phase 16)
        background_tasks.add_task(drift_monitor.check, [request.text], [result['prediction']])
        
        # Phase 61: Alerting
        if result.get("security_risk_score", 0) >= 75:
            from src.security.alerts import trigger_security_alert
            background_tasks.add_task(trigger_security_alert, "Phishing Detection", result)
        
        return result
    except Exception as e:
        logger.error("Prediction error: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-security")
async def analyze_security_endpoint(body: PredictRequest):
    """Phase 49: Detailed security analysis without ML prediction."""
    from src.security.risk_scoring import calculate_security_risk
    try:
        analysis = calculate_security_risk(body.text, body.headers or "")
        return analysis
    except Exception as e:
        logger.error("Security analysis error: %s", e)
        raise HTTPException(status_code=500, detail="Security scanning failed")


@app.post("/predict/batch")
async def predict_batch_endpoint(body: BatchPredictRequest, request: Request, user: str = Depends(optional_auth)):
    try:
        results = predict_batch(body.emails, body.model_name)
        return {"results": results, "count": len(results)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Batch prediction error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal prediction error")


@app.post("/export-report")
async def export_report_endpoint(body: PredictRequest):
    """Phase 63: Forensic Analysis Export."""
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


# ---------------------------------------------------------------------------
# Feedback endpoint
# ---------------------------------------------------------------------------

@app.post("/feedback")
async def submit_feedback(body: FeedbackRequest):
    # Compliance: Anonymize feedback text before saving
    clean_text = anonymize_text(body.email_text)

    entry = save_feedback(
        email_text=clean_text,
        predicted_label=body.predicted_label,
        correct_label=body.correct_label,
        model_used=body.model_used,
    )

    # Record outcome for A/B testing
    ab_test.record(body.model_used, body.predicted_label, body.correct_label)
    ab_test.save()

    return {"status": "recorded", "feedback_total": feedback_count(), "entry": entry}


# ---------------------------------------------------------------------------
# A/B Testing summary
# ---------------------------------------------------------------------------

@app.get("/ab/summary")
async def get_ab_summary():
    return ab_test.summary()


# ---------------------------------------------------------------------------
# Analytics endpoint
# ---------------------------------------------------------------------------

@app.get("/analytics")
async def analytics():
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "metrics.json")
    if not os.path.exists(metrics_path):
        return {"error": "No metrics available. Train models first."}
    with open(metrics_path) as f:
        data = json.load(f)
    return data


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/register")
async def register(body: RegisterRequest):
    try:
        result = register_user(body.username, body.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/auth/login")
async def login(body: LoginRequest):
    result = authenticate_user(body.username, body.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


# ---------------------------------------------------------------------------
# Health & Readiness
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/health/ready")
async def readiness():
    """Check that models and vectorizer are loaded and ready to serve."""
    models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
    vec_ok = os.path.exists(os.path.join(models_dir, "vectorizer.pkl"))
    metrics_ok = os.path.exists(os.path.join(models_dir, "metrics.json"))

    ready = vec_ok and metrics_ok
    detail = {
        "vectorizer_loaded": vec_ok,
        "metrics_available": metrics_ok,
        "status": "ready" if ready else "not_ready",
    }
    if not ready:
        raise HTTPException(status_code=503, detail=detail)
    return detail
