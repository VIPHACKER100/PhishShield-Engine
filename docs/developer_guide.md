# PhishShield-Engine: Comprehensive Developer Guide

## Overview

This document provides exhaustive documentation on the architecture, command-line interfaces, security subsystems, and maintenance procedures for the **PhishShield-Engine** platform.

---

## Installation & Build

### 1. Local Environment Setup

```bash
# Initialize Virtual Environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install All Dependencies
pip install -r requirements.txt

# Run Database Migrations
alembic upgrade head
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and set your configuration variables:

```bash
# Generate a cryptographically strong secret for JWT signing
python -c "import secrets; print(secrets.token_hex(32))"
```

In `.env`:
```env
JWT_SECRET=<generated_secret>
JWT_EXPIRY_HOURS=1
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15
RESET_TOKEN_EXPIRY_HOURS=1
ENV=prod
```

### 3. Model Initialization

You must initialize your models before the first run. For a full deep-dive into the training lifecycle, see the [ML Training Guide](ML_TRAINING_GUIDE.md).

```bash
# Recommendation: Quick-start on 50,000 samples (fast mode)
python scripts/train_pipeline.py --generate --fast
```

---

## Command Reference

### I. The Management CLI (`manage.py`)

Used for day-to-day operations and threat intelligence management.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `serve` | `--port <val>` | Launches the cinematic security dashboard. |
| `block` | `<domain> [--reason <str>]` | Manually injects a domain into the threat intelligence blocklist. |
| `metrics` | (None) | Aggregates local threat DB statistics and model health. |

**Example Usage:**

```bash
python cli/manage.py block evil-hacker.com --reason "Active credential harvesting detected"
```

### II. The Training Pipeline (`train_pipeline.py`)

Handles the entire ML lifecycle from raw data to registered production models.

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--dataset_path` | `data/raw/emails.csv` | Path to the training dataset. |
| `--vectorizer` | `tfidf` | Algorithm: `tfidf`, `bow`, or `tfidf_char`. |
| `--sample_size` | (None) | Sub-sample N rows (prevents OOM on large datasets). |
| `--fast` | (False) | Shortcut: 50k samples + Skip Ensemble. |
| `--tune` | (False) | Triggers RandomizedSearchCV tuning. |
| `--ensemble` | (False) | Trains model ensembles (`voting` or `stacking`). |
| `--ensemble_kind` | `voting` | Choose `voting` (fast) or `stacking` (accurate). |
| `--generate` | (False) | Generates synthetic phishing samples. |

### III. Operational Scripts

* **`python scripts/retrain_scheduler.py`**: Background daemon that monitors `data/feedback.db`. Triggers retraining once new feedback exceeds the threshold.
* **`python scripts/chaos_monkey.py`**: Injects faults (ML model corruption, load spikes) to verify graceful degradation.
* **`python scripts/backup.py backup`**: Creates a timestamped snapshot of models, threat DBs, and configs.

---

## Authentication & Security Subsystems

### 1. Authentication Architecture (`src/api/auth.py`)

- **Password Hashing**: Utilizes `bcrypt` with salt generation (`gensalt()`). Enforces password complexity:
  - Minimum 8 characters
  - At least 1 numeric digit
  - At least 1 special character (`!@#$%^&*...`)
- **Session & JWT Management**: Issues short-lived JWTs (default 1 hour expiry) with `sub`, `iat`, `exp`, and `jti` claims. Secrets are managed via `SecretsVault` with environment-variable precedence.
- **Brute-Force Lockout**: Tracks `failed_login_attempts` per user. Reaching 5 failures locks the account for 15 minutes (`locked_until`).
- **Timing Attack Mitigation**: Employs constant-time string comparison (`hmac.compare_digest`) for API key verification (`pse_` prefix) and executes dummy password hashes for non-existent users.
- **Password Reset Flow**: `request_password_reset` issues a single-use token (`secrets.token_urlsafe(32)`). Only SHA-256 digests (`password_reset_token_hash`) and expirations (`password_reset_expires`) are stored in the database.
- **Insecure Direct Object Reference (IDOR) Defense**: All user resource queries (`GET /auth/me`, `GET /auth/logs`, `GET /auth/logs/{log_id}`, `GET /auth/feedback/{feedback_id}`, `DELETE /auth/feedback/{feedback_id}`) filter strictly by `resource.user_id == current_user.id`. Accessing unowned resources returns `404 Not Found` without disclosing resource existence.

### 2. Rate Limiting (`SlowAPI`)

- `/auth/login`: 5 requests/min per IP
- `/auth/register`: 3 requests/min per IP
- `/auth/password-reset-request`: 3 requests/min per IP
- `/auth/password-reset`: 5 requests/min per IP
- Global API limit: 60 requests/min per IP

### 3. Database Schema & Migrations (`src/core/database.py`, `alembic/`)

The `users` table includes security governance fields:
- `username`, `password_hash`, `api_key`
- `email` (optional, unique)
- `is_email_verified` (boolean flag)
- `failed_login_attempts` (integer counter)
- `locked_until` (datetime)
- `password_reset_token_hash` (string)
- `password_reset_expires` (datetime)

Schema revisions are maintained via Alembic (`alembic/versions/8eb220da558a8768_add_auth_security_fields.py`).

### 4. Forensic Intelligence Layer

The `calculate_security_risk` function (in `src/security/risk_scoring.py`) executes 10 independent forensic scans:

* **Obfuscation Scan**: Detects zero-width icons/markers via `src/security/obfuscation_detector.py`.
* **Homograph Scan**: Identifies "lookalike" Unicode domains (punycode detection).
* **Mixed-Script Detection**: Identifying "lookalike" characters from Latin, Greek, and Cyrillic scripts.
* **Brand Protection**: Fuzzy-matches against 15+ high-value target brands.
* **Header Forensics**: SPF/DKIM/DMARC validation and `Return-Path` analysis.
* **Domain Intel**: Local SQLite lookup of known malicious domains.
* **IP-Based URLs**: Detecting raw IP addresses in message links.
* **Suspicious URLs**: Heuristic analysis of URL entropy and path patterns.
* **Behavioral Threat**: Statistical mapping of text-based threat indicators.
* **Cyrillic URL Spoofing**: Detects Cyrillic characters embedded in URLs (weight: 50).

### 5. Governance-as-Code (`config/config.yaml`)

Control the engine's behavior without modifying code:

* **Weights**: Adjust the risk contribution of each forensic flag (including `cyrillic_url: 50`).
* **Thresholds**: Define "High Risk" and "Suspicious" cutoffs.
* **Compliance**: Define auto-retention days (Default: 30 days).

---

## Production Orchestration (Docker)

The platform is designed to run as a multi-service architecture using **Docker Compose**:

```bash
# Launch API, Threat DB, and Retraining Scheduler (with model training)
docker-compose up --build -d

# Or build without training (use pre-trained models from models/ directory)
docker build --target base -t phishshield-base .
docker-compose up -d
```

* **Service API**: Exposes the port `8000`.
* **Service Scheduler**: Runs the automated retraining watcher.
* **Persistence**: Volumes are mapped for `data/` and `logs/` to prevent loss during restarts.
* **Training Control**: Set `TRAIN_MODELS=false` build arg to skip training during image build (use pre-trained models).

---

## Testing & Quality Assurance

* **Unit & Security Tests**: `python -m pytest tests/` or `python -m pytest tests/test_auth_unit.py -v`
* **Integration Tests**: `python scripts/chaos_monkey.py` (Simulates failure scenarios)
* **Compliance Audit**: View `logs/compliance.log` to audit data retention and forensic overrides.
* **Warning Suppression**: Tests use `tests/conftest.py` to suppress httpx deprecation and LGBM feature name warnings.

---

## Maintainer

**VIPHACKER100 (Aryan Ahirwar)**  
*Cybersecurity Researcher | AI Security Lead*  
*Last Updated: 2026-09-02*
