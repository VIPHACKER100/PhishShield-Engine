"""
FastAPI Application — Main API server with prediction, batch, analytics,
authentication, rate limiting, and security hardening.
"""

import os
import time
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.utils.logger import logger, generate_request_id
from src.api.routers import auth, predict, analytics
from src.core.database import init_db

# ---------------------------------------------------------------------------
# Lifespan — run setup/teardown around the app lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):
    """Initialize database tables on startup."""
    init_db()
    logger.info("Database tables initialized.")
    yield

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Email Spam Classifier API",
    description="Classify emails as Spam or Ham using ML models.",
    version="2.0.0",
    lifespan=lifespan,
)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(analytics.router)

# Expose prometheus metrics
Instrumentator().instrument(app).expose(app)

# ---------------------------------------------------------------------------
# Rate limiting (SlowAPI)
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------------------------
# Middleware — request ID
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    req_id = generate_request_id()
    request.state.request_id = req_id
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
