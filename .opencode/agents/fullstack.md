# Fullstack Agent

## Purpose

Handles API development (FastAPI), CLI tooling (manage.py), frontend templates (Jinja2), Gmail integration, authentication (JWT/bcrypt), schema design (Pydantic), database interactions (SQLAlchemy), and all integration/linking between the ML and security layers.

## Project Context

PhishShield-Engine exposes a FastAPI-based RESTful API with JWT authentication, rate limiting (SlowAPI), Prometheus metrics, and ARQ-backed async background jobs. The CLI (`cli/manage.py`) provides operational commands. The system integrates with Gmail via OAuth2 for automated inbox scanning. All database interactions use SQLAlchemy ORM with SQLite (dev) or PostgreSQL (prod).

## Relevant Directories

| Directory | Purpose |
|-----------|---------|
| `src/api/` | FastAPI app, routers, schemas, auth, dependencies, templates |
| `src/api/app.py` | Main FastAPI application (lifespan, middleware, routes) |
| `src/api/routers/` | Route handlers (auth.py, predict.py, analytics.py) |
| `src/api/schemas.py` | Pydantic request/response models |
| `src/api/auth.py` | JWT + bcrypt authentication |
| `src/api/dependencies.py` | DI (AB testing, optional auth) |
| `src/core/database.py` | SQLAlchemy models (User, UsageLog, Feedback) |
| `src/core/worker.py` | ARQ background worker settings |
| `src/integrations/gmail_client.py` | Gmail API OAuth2 scanning client |
| `src/utils/` | Config loader, secrets, logger, compliance, anonymizer |
| `cli/manage.py` | CLI management tool (serve, block, metrics) |
| `data/` | SQLite databases (app.db, auth.db, feedback.db, phishshield.db) |
| `tests/test_api.py` | API integration tests |

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login, receive JWT |
| POST | `/predict` | No* | Classify email (ML + security) |
| POST | `/predict/batch` | Optional | Batch classify up to 100 emails |
| POST | `/analyze-security` | No | Forensic analysis only (no ML) |
| POST | `/export-report` | No | Full forensic export report |
| POST | `/feedback` | No | Submit user feedback correction |
| GET | `/analytics` | No | Model performance metrics |
| GET | `/ab/summary` | No | A/B testing split summary |
| GET | `/health` | No | System health |
| GET | `/health/ready` | No | Readiness (model + vectorizer loaded) |
| GET | `/metrics` | No | Prometheus metrics |
| GET | `/docs` | No | Swagger UI |
| GET `/redoc` | No | ReDoc UI |

*Auth recommended but not enforced in current configuration.

## Common Workflows

### Start the development server

```bash
python cli/manage.py serve
# or
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### Start on a custom port

```bash
python cli/manage.py serve --port 8080
```

### Quick prediction test via curl

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Urgent: Your account has been locked. Click http://evil.com to verify.", "model": "random_forest"}'
```

### Test batch prediction

```bash
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"emails": ["Free money now!", "Meeting at 3pm today"], "model_name": "naive_bayes"}'
```

### Analyze security only (no ML)

```bash
curl -X POST http://localhost:8000/analyze-security \
  -H "Content-Type: application/json" \
  -d '{"text": "http://192.168.1.1/login", "headers": "From: support@paypa1.com"}'
```

### Submit feedback for retraining

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"email_text": "Free money now", "predicted_label": "ham", "correct_label": "spam", "model_used": "naive_bayes"}'
```

### Register and authenticate

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "securepass123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "securepass123"}'
```

### Block a domain via CLI

```bash
python cli/manage.py block evil-domain.com --reason "Detected in phishing campaign"
```

### View system metrics via CLI

```bash
python cli/manage.py metrics
```

### Run API tests

```bash
python -m pytest tests/test_api.py -v
```

### Export a forensic report

```bash
curl -X POST http://localhost:8000/export-report \
  -H "Content-Type: application/json" \
  -d '{"text": "Urgent payment required at http://bit.ly/abc", "headers": "From: invoice@paypa1.com"}'
```

### Gmail integration setup

```bash
# Configure OAuth2 credentials (see docs/GMAIL_INTEGRATION.md)
# Then trigger scan:
python -c "from src.integrations.gmail_client import scan_inbox; scan_inbox()"
```

### Access interactive API docs

```
http://localhost:8000/docs    # Swagger UI
http://localhost:8000/redoc   # ReDoc
```

## Key Code Patterns

### Adding a new API endpoint

1. Create route handler in `src/api/routers/` (or add to existing router file)
2. Define Pydantic schema in `src/api/schemas.py`
3. Register router in `src/api/app.py` via `app.include_router()`
4. Add tests in `tests/test_api.py`

### Database schema changes

1. Define/modify SQLAlchemy model in `src/core/database.py`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Apply: `alembic upgrade head`

### Configuration changes

All API-level settings (rate limit, max text length, port) are in `config/config.yaml` under the `api:` key and loaded via `src/utils/config_loader.py`.
