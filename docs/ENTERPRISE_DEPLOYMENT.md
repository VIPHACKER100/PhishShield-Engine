# PhishShield-Engine: Enterprise Operations Guide

The architecture of **PhishShield-Engine** implements rigorous operations governance for large-scale enterprise deployments. This document describes the disaster recovery, logging, analytics, zero-trust security controls, and intelligence lifecycle components natively running underneath the ML pipeline.

---

## 1. Secrets Management API & Zero-Trust Auth

To keep private tokens, database connections, and internal JWT signing keys isolated from source code, PhishShield relies completely on `src/utils/secrets.py` and a hardened authentication architecture.

### Secrets Vault Priority

1. **Environment Variables (Highest Priority)**: Read directly from process environment (e.g. `export JWT_SECRET=...`, `export DATABASE_URL=...`).
2. **Local Fallback (`config/secrets.json`)**: Used strictly for local dev convenience (`.gitignored`). Loaded *before* environment variables so environment variables always win.

> 🔒 **Production Startup Guard**: When `ENV=prod`, the application will immediately fail to start with a `RuntimeError` if `JWT_SECRET` is unconfigured or uses the default development placeholder string (`email-classifier-dev-secret-change-in-prod`).

### Authentication Security Controls

- **Password Hashing**: Passwords are hashed using `bcrypt` with automatic salt generation (`gensalt()`). Passwords must be at least 8 characters long and contain at least one digit and one special character.
- **Short-Lived JWT Tokens**: Signed using `HS256` with 1-hour expiration by default (`JWT_EXPIRY_HOURS=1`). Each token includes unique `jti` (JWT ID) and `iat` (Issued At) claims.
- **Brute-Force & Lockout Protection**: Accounts are automatically locked for 15 minutes (`LOGIN_LOCKOUT_MINUTES=15`) after 5 consecutive failed login attempts (`LOGIN_MAX_ATTEMPTS=5`).
- **User Enumeration Defense**: Constant-time dummy `bcrypt` verification on unknown usernames to prevent timing attacks. All authentication failure responses return a generic `401 Unauthorized` ("Invalid credentials").
- **API Key Hardening**: API keys use the `pse_` prefix and are evaluated using constant-time string comparison (`hmac.compare_digest`).
- **Secure Password Reset**: One-time reset tokens generated via `secrets.token_urlsafe(32)` expire after 1 hour (`RESET_TOKEN_EXPIRY_HOURS=1`). Only the SHA-256 hash of the token is stored in the database.
- **Per-Endpoint Rate Limiting**: Enforced via `SlowAPI`:
  - `POST /auth/login`: 5 requests/minute per IP
  - `POST /auth/register`: 3 requests/minute per IP
  - `POST /auth/password-reset-request`: 3 requests/minute per IP
  - `POST /auth/password-reset`: 5 requests/minute per IP

---

## 2. Automated Model Lifecycle (MLOps) & Processing

The internal Machine Learning ecosystem governs its own drift, monitoring, and validation.

- **Background Queueing (ARQ & Redis):** High-latency predictions and background tasks (like `check_drift` and `trigger_security_alert`) are decoupled from the FastAPI request cycle using **ARQ** backed by Redis.
- **A/B Testing:** Multi-pipeline inference runs internally handled by `src/models/ab_testing.py` where traffic can dynamically split between Naive Bayes, SVM, and Transformers.
- **Retrain Daemon:** `scripts/retrain_scheduler.py` is an asynchronous worker. It analyzes records in `data/feedback.db` (SQLite) and initiates GridSearch without server downtime. Feedback is also mirrored to `data/feedback/feedback_data.csv`.
- **Deep Learning Architecture Base:** `src/models/deep_learning.py` runs Transformer pipelines (`bert-base-uncased`) and leverages ChromaDB semantic caching to avoid repeated inferences.

---

## 3. Analytics, Explainability (XAI), & Observability

For cybersecurity analysts reviewing inbound traffic spikes:

- `POST /export-report`: Compiles an immediately readable mapping merging all 10 active Forensic Rules (including `cyrillic_url`) alongside the Scikit-learn outputs.
- `GET /metrics`: Native **Prometheus** endpoint exposing model inference latencies, API request rates, and active threat detection histograms. Ideal for Grafana integrations.
- **SHAP Integration:** The XAI pipeline utilizes `shap.LinearExplainer` to explicitly assign weight and threat contribution to individual tokens in the email body.
- **Unified DB Migrations**: Schema evolution (such as security columns for failed login counters, lockout timestamps, and password reset tokens) is managed deterministically via **Alembic** (`alembic upgrade head`).

---

## 4. Docker Optimization

For enterprise environments requiring fast CI/CD builds, the Docker image includes conditional build parameters and environment injection.

- **Environment Injection:** Requires a strictly formatted `.env` file containing Postgres/SQLite `DATABASE_URL`, `REDIS_HOST`, and production `JWT_SECRET`.
- **Fast Build (Default):** Skips local model retraining (`docker build .`).
- **Full Build:** Trains the ensemble locally within the build container by passing `--build-arg TRAIN_MODELS=true`.

---

## 5. Chaos Monkey & Production Load Testing

To ensure reliability scaling past standard 60-RPM environments limiters:

- We deploy `scripts/benchmark.py` which triggers `asyncio` parallel threading designed to rapidly bombard the `POST /predict/batch` endpoint.
- PhishShield-Engine handles up to 10,000 parallel multi-email bulk arrays utilizing Uvicorn multi-threading and ARQ task distribution.
- During severe instance failure, `scripts/restore_backup.py` pulls active Vectorizer, Models, and Model Registry configurations out of `/backups`.

---

**Maintainer**: VIPHACKER100 (Aryan Ahirwar)  
**Last Updated**: 2026-09-02
