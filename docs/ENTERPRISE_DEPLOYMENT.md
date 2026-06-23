# 🏛️ PhishShield-Engine: Enterprise Operations Guide

The architecture of **PhishShield-Engine** implements rigorous operations governance for large-scale enterprise deployments. This document describes the disaster recovery, logging, analytics, and intelligence lifecycle components natively running underneath the ML pipeline.

---

## 🔐 1. Secrets Management API (Zero-Trust)

To keep private tokens, OpenAI fallbacks, and internal JWT signing keys isolated from source code, PhishShield relies completely on `src/utils/secrets.py`.

### How It Works

- Keys are aggressively populated directly from system-level hardware environments (e.g. `export APP_SECRET_KEY=XYZ`).
- Secondary fallback resides inside `config/secrets.json` (Which is automatically `.gitignored` to prevent token leakage).
- All API and DB components interface via `vault.get("JWT_SECRET")`.

---

## 📈 2. Automated Model Lifecycle (MLOps) & Processing

The internal Machine Learning ecosystem governs its own drift, monitoring, and validation.

- **Background Queueing (ARQ & Redis):** High-latency predictions and background tasks (like `check_drift` and `trigger_security_alert`) are decoupled from the FastAPI request cycle using **ARQ** backed by Redis.
- **A/B Testing:** Multi-pipeline inference runs internally handled by `src/models/ab_testing.py` where traffic can dynamically split between Naive Bayes, SVM, and Transformers.
- **Retrain Daemon:** `scripts/retrain_scheduler.py` is an asynchronous worker. It analyzes records in `data/feedback.db` (SQLite) and initiates GridSearch without server downtime. Feedback is also mirrored to `data/feedback/feedback_data.csv`.
- **Deep Learning Architecture Base:** `src/models/deep_learning.py` runs Transformer pipelines (`bert-base-uncased`) and leverages ChromaDB semantic caching to avoid repeated inferences.

---

## 📡 3. Analytics, Explainability (XAI), & Observability

For cybersecurity analysts reviewing inbound traffic spikes:

- `POST /export-report`: Compiles an immediately readable mapping merging all 10 active Forensic Rules (including `cyrillic_url`) alongside the Scikit-learn outputs.
- `GET /metrics`: Native **Prometheus** endpoint exposing model inference latencies, API request rates, and active threat detection histograms. Ideal for Grafana integrations.
- **SHAP Integration:** The XAI pipeline utilizes `shap.LinearExplainer` to explicitly assign weight and threat contribution to individual tokens in the email body.
- **Unified DB Migrations:** Schema evolution (like adding new feedback columns) is managed deterministically via **Alembic**, ensuring zero-downtime database upgrades.

---

## 🐳 4. Docker Optimization

For enterprise environments requiring fast CI/CD builds, the Docker image includes conditional build parameters and environment injection.

- **Environment Injection:** Requires a strictly formatted `.env` file containing Postgres/SQLite `DATABASE_URL` and `REDIS_URL`.
- **Fast Build (Default):** Skips local model retraining (`docker build .`).
- **Full Build:** Trains the ensemble locally within the build container by passing `--build-arg TRAIN_MODELS=true`.

---

## ⛓️ 5. Chaos Monkey & Production Load Testing

To ensure reliability scaling past standard 60-RPM environments limiters:

- We deploy `scripts/benchmark.py` which triggers `asyncio` parallel threading designed to rapidly bombard the `POST /predict/batch` endpoint.
- PhishShield-Engine handles up to 10,000 parallel multi-email bulk arrays utilizing Uvicorn multi-threading and ARQ task distribution.
- During severe instance failure, `scripts/restore_backup.py` pulls active Vectorizer, Models, and Model Registry configurations out of `/backups`.

---

**Maintainer**: VIPHACKER100 (Aryan Ahirwar)
**Last Updated**: 2026-06-22
