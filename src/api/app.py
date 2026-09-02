"""
FastAPI Application — Main API server with prediction, batch, analytics,
authentication, rate limiting, security headers, and security audit logging.
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.utils.logger import logger, security_logger, log_security_event, generate_request_id
from src.api.routers import auth, predict, analytics
from src.core.database import init_db

_ENV = os.environ.get("ENV", "dev").lower()
_ENFORCE_HTTPS = os.environ.get("ENFORCE_HTTPS", "false").lower() in ("true", "1")

# ---------------------------------------------------------------------------
# Lifespan — run setup/teardown around the app lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):
    """Initialize database tables on startup."""
    init_db()
    logger.info("Database tables initialized.")
    log_security_event("SYSTEM_STARTUP", "127.0.0.1", "system", f"Environment: {_ENV}")
    yield

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PhishShield Engine API",
    description="Classify emails as Spam or Ham using ML models and multi-layered security heuristics.",
    version="3.1.0",
    lifespan=lifespan,
    docs_url="/docs" if _ENV != "prod" else None,     # Disable Swagger UI in production unless configured
    redoc_url="/redoc" if _ENV != "prod" else None,   # Disable ReDoc in production unless configured
)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(analytics.router)

# Expose prometheus metrics
Instrumentator().instrument(app).expose(app)

# HTTPS Enforcement Middleware in production or when explicitly enabled
if _ENFORCE_HTTPS or (_ENV == "prod" and os.environ.get("ENABLE_HTTPS_REDIRECT", "false").lower() == "true"):
    app.add_middleware(HTTPSRedirectMiddleware)

# ---------------------------------------------------------------------------
# Rate limiting & RateLimitExceeded Security Logging
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter


async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    client_ip = get_remote_address(request)
    log_security_event(
        "RATE_LIMIT_EXCEEDED",
        client_ip=client_ip,
        detail=f"Path={request.url.path} Limit={exc.detail}"
    )
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please slow down your requests."}
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------------------------
# Middleware — Request ID, Security Headers, and Error Audit Logging
# ---------------------------------------------------------------------------

@app.middleware("http")
async def security_and_request_middleware(request: Request, call_next):
    req_id = generate_request_id()
    request.state.request_id = req_id
    client_ip = get_remote_address(request)
    start = time.time()

    response = await call_next(request)
    duration = round(time.time() - start, 3)

    logger.info(
        "[%s] %s %s → %s (%.3fs)",
        req_id, request.method, request.url.path, response.status_code, duration,
        extra={"request_id": req_id},
    )

    # Security Headers
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:;"
    )

    # Log API errors or unusual response status codes to security audit log
    if response.status_code >= 500:
        log_security_event(
            "SERVER_ERROR",
            client_ip=client_ip,
            detail=f"Method={request.method} Path={request.url.path} Status={response.status_code}"
        )
    elif response.status_code in (400, 401, 403, 404, 422):
        log_security_event(
            "CLIENT_ERROR",
            client_ip=client_ip,
            detail=f"Method={request.method} Path={request.url.path} Status={response.status_code}"
        )

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
