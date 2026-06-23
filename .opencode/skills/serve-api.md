# Skill: Serve the FastAPI Server

## Description

Starts the PhishShield-Engine FastAPI server locally or via Docker Compose, including all API endpoints, Prometheus metrics, Swagger documentation, and background worker services.

## Prerequisites

- Python environment with dependencies installed (`pip install -r requirements.txt`)
- For Docker deployment: Docker and Docker Compose installed
- Models must be initialized (`python scripts/train_pipeline.py --generate --fast`)
- Working directory at project root

## Workflow Steps

### 1. Start local development server

```bash
# Using the management CLI (auto-reload enabled)
python cli/manage.py serve
# Server starts at http://localhost:8000
```

### 2. Start on custom port

```bash
python cli/manage.py serve --port 8080
```

### 3. Start with uvicorn directly

```bash
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Start Docker Compose (full stack)

```bash
# Build and start all services
docker-compose up --build -d

# Check all services are running
docker-compose ps

# View API logs
docker-compose logs -f api
```

### 5. Start with minimal services (API + Redis only)

```bash
docker-compose up -d api redis
```

### 6. Start without model training

```bash
docker build --target base -t phishshield-base .
docker-compose up -d
```

## Verification

### Check server is running

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Readiness check
curl http://localhost:8000/health/ready
# Expected: {"vectorizer_loaded": true, "metrics_available": true, "status": "ready"}
```

### Test prediction endpoint

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Free money! Click http://bit.ly/xyz"}'
```

### Check Prometheus metrics

```bash
curl http://localhost:8000/metrics
```

### Open API documentation

```
http://localhost:8000/docs    # Swagger UI
http://localhost:8000/redoc   # ReDoc
```

### Verify Docker services

```bash
# List all running containers
docker-compose ps
```

## Available Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | No | Home page (PhishShield dashboard) |
| GET | `/dashboard` | No | Security dashboard |
| GET | `/health` | No | System health |
| GET | `/health/ready` | No | Readiness check |
| GET | `/metrics` | No | Prometheus metrics |
| POST | `/predict` | No | Email classification |
| POST | `/predict/batch` | Optional | Batch classification |
| POST | `/analyze-security` | No | Forensic analysis |
| POST | `/export-report` | No | Forensic export |
| POST | `/feedback` | No | Submit feedback |
| POST | `/auth/register` | No | User registration |
| POST | `/auth/login` | No | User login |
| GET | `/analytics` | No | Model metrics |
| GET | `/ab/summary` | No | A/B test summary |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Activate venv and run `pip install -r requirements.txt` |
| `Vectorizer not found` | Run `python scripts/train_pipeline.py --generate --fast` first |
| Port already in use | Use `--port 8080` or change in `config/config.yaml` |
| Docker permission denied | Run Docker commands with appropriate privileges |
| Redis connection refused | Start Redis: `docker run -d -p 6379:6379 redis:7-alpine` or use `docker-compose up -d redis` |
| Database errors | Check `.env` has correct `DATABASE_URL`, or delete `data/app.db` to reset |

## Related Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (default admin/admin)
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432
