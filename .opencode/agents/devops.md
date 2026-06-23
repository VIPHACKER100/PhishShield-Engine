---
description: Docker, Docker Compose, CI/CD, database migrations, monitoring, and infrastructure
mode: subagent
permission:
  read: allow
  edit: allow
  bash: allow
---

# DevOps Agent

## Purpose

Manages Docker containerization, Docker Compose orchestration, CI/CD pipelines (GitHub Actions), database migrations (Alembic), infrastructure configuration, Prometheus/Grafana observability, backup/restore operations, and production deployment of the PhishShield-Engine platform.

## Project Context

PhishShield-Engine is deployed as a multi-service architecture with 6 containers: API server (FastAPI/Uvicorn), ARQ worker (background tasks), retrain scheduler, Redis (async queue), PostgreSQL (production DB), Prometheus (metrics), and Grafana (visualization). The system supports both SQLite (dev) and PostgreSQL (prod) database backends.

## Relevant Directories

| Directory | Purpose |
|-----------|---------|
| `Dockerfile` | Multi-stage Docker build (builder + final) |
| `docker-compose.yml` | Multi-service orchestration (6 services) |
| `config/` | Global configuration (config.yaml, prometheus.yml, alert_rules.yml) |
| `config/prometheus.yml` | Prometheus scrape configuration |
| `config/alert_rules.yml` | Prometheus alerting rules |
| `.env.example` | Environment variable template |
| `alembic/` | Database migration scripts |
| `alembic.ini` | Alembic configuration |
| `.github/workflows/ci.yml` | CI pipeline (tests, lint, security scan, Docker build) |
| `.github/workflows/codeql.yml` | CodeQL security analysis |
| `scripts/backup.py` | Backup automation |
| `scripts/restore_backup.py` | Restore from backup |
| `scripts/chaos_monkey.py` | Fault injection / resilience testing |
| `scripts/benchmark.py` | Load testing tool |
| `data/` | Persistent data volumes (DBs, threat intel, feedback) |
| `logs/` | Application logs (app.log, compliance.log, incidents.log) |
| `models/` | Trained model artifacts (persistent) |

## Service Architecture

```
┌─────────────┐     ┌──────────────┐
│   FastAPI    │────▶│    Redis     │
│  (Port 8000) │     │  (Port 6379) │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────┐   ┌───────────────┐
│  PostgreSQL  │   │ ARQ Worker    │
│  (Port 5432) │   │ + Scheduler   │
└──────────────┘   └───────────────┘

┌──────────────┐   ┌───────────────┐
│  Prometheus  │   │   Grafana     │
│  (Port 9090) │   │  (Port 3000)  │
└──────────────┘   └───────────────┘
```

## Common Workflows

### Full stack deployment

```bash
# Start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f scheduler
```

### Build without model training (fast)

```bash
docker build --target base -t phishshield-base .
docker-compose up -d
```

### Build with model training included

```bash
docker-compose build --build-arg TRAIN_MODELS=true
docker-compose up -d
```

### Run database migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "description of change"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backup and restore

```bash
# Create a timestamped backup of models, threat DBs, and configs
python scripts/backup.py backup

# Restore from latest backup
python scripts/restore_backup.py --latest
```

### Chaos engineering (fault injection)

```bash
# Injects faults (ML model corruption, load spikes) to test resilience
python scripts/chaos_monkey.py
```

### Load testing

```bash
# Stress test the /predict/batch endpoint with parallel requests
python scripts/benchmark.py
```

### CI/CD commands

```bash
# Run the full CI pipeline locally (Black, Flake8, Bandit, tests)
pip install black flake8 bandit
black --check src/ tests/
flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
bandit -r src/ -ll -ii
python -m pytest tests/ -v --tb=short
```

### Prometheus & Grafana

```bash
# Prometheus UI
open http://localhost:9090

# Grafana UI (default admin/admin)
open http://localhost:3000

# API metrics endpoint
curl http://localhost:8000/metrics
```

### Production environment variables (`.env`)

```bash
DATABASE_URL=postgresql://user:pass@postgres:5432/phishshield
REDIS_HOST=redis
REDIS_URL=redis://redis:6379
JWT_SECRET=your-secret-key
APP_SECRET_KEY=your-app-secret
```

### Application health checks

```bash
# Health check
curl http://localhost:8000/health

# Readiness check (checks vectorizer + metrics availability)
curl http://localhost:8000/health/ready

# Swagger documentation
open http://localhost:8000/docs
```

### Monitoring logs

```bash
# Application log
tail -f logs/app.log

# Compliance audit log (GDPR retention)
tail -f logs/compliance.log

# Security incident log
tail -f logs/incidents.log

# A/B test results
cat logs/ab_test_results.json
```

## Infrastructure Notes

- **Database**: SQLite for local dev (`data/app.db`), PostgreSQL in production via `DATABASE_URL` env var
- **Queue**: ARQ backed by Redis for async tasks (drift checking, security alerts)
- **Rate Limiting**: SlowAPI middleware, 60 requests/minute default
- **Observability**: Prometheus instrumentator exposes request count, latency histograms at `/metrics`
- **Health Check**: Docker HEALTHCHECK pings `/health` every 30s
- **Volumes**: `data/` and `logs/` are mapped as Docker volumes for persistence
