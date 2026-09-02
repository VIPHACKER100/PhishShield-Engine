# PhishShield-Engine

**PhishShield-Engine** is an AI-powered email security platform designed to detect spam, phishing attacks, malicious URLs, homograph spoofing, and identity impersonation using advanced machine learning, zero-trust authentication, multi-layer forensic intelligence, and strict input sanitization.

---

## GitHub Repository

```text
PhishShield-Engine
```

---

## Short Description

AI-powered email security engine that identifies spam, phishing, and identity spoofing using ensemble machine learning and advanced cybersecurity heuristics.

> **“Smart AI defense for your inbox.”**

---

## Key Technical Features

### Core Security Intelligence

- **Phishing Detection**: Specialized logic for identifying social engineering and credential theft attempts.
- **Obfuscation Defense**: Advanced detection of zero-width characters and hidden markers used to bypass traditional filters.
- **Homograph Attack Protection**: Identifies IDN (Internationalized Domain Name) attacks, Cyrillic alphabet URL spoofing, and Unicode-based visual spoofing.
- **Fuzzy Brand Protection**: Detects impersonation of 15+ major global brands (PayPal, Amazon, Google, etc.).
- **Header Forensics**: Deep validation of SPF/DKIM/DMARC and detection of sender-domain mismatches.

### Hardened Authentication, Zero-Trust & Input Sanitization

- **Input Validation & Sanitization (`src/utils/sanitizer.py`)**: Automatic null-byte stripping, ASCII control-character removal, HTML tag escaping (`html.escape`), and strict regex constraints on usernames (`^[a-zA-Z0-9_-]{3,50}$`), domains, and tokens to neutralize Stored/Reflected XSS and SQL injection attempts.
- **Bcrypt DoS Defense**: 128-character cap on all password fields to prevent CPU denial-of-service vector attacks.
- **Secure Password Hashing**: Passwords hashed with `bcrypt` work-factor salting. Enforces 8+ characters with numeric digit and special symbol requirements.
- **Short-Lived JWT Sessions**: Signed via `PyJWT` with 1-hour expiration, including unique `jti` and `iat` claims.
- **Brute-Force & Lockout Protection**: Automatic account lockout after 5 consecutive failed attempts (`LOGIN_LOCKOUT_MINUTES=15`).
- **Timing Attack & Enumeration Defenses**: Constant-time `hmac.compare_digest` for `pse_` API keys and dummy `bcrypt` operations for non-existent users.
- **Abuse & Bot Protection**: Per-endpoint rate limiting via `SlowAPI`, empty `User-Agent` blocking, 14-tool scanner blacklist (`sqlmap`, `nikto`), and honeypot header/payload traps.
- **Secure Password Reset**: One-time reset tokens (`secrets.token_urlsafe(32)`) expiring in 1 hour; only SHA-256 digests are stored in DB.
- **Production Secrets Vault**: Env-first secret management (`src/utils/secrets.py`) with mandatory production startup guards preventing weak/default `JWT_SECRET` keys.

### Machine Learning Engine

- **Ensemble Intelligence**: High-performance voting classifier combining Naive Bayes, SVM, and Random Forests.
- **Deep Learning & RAG**: Transformer-based inference (`bert-base-uncased`) augmented by ChromaDB-powered Vector Search for semantic threat matching.
- **Quantitative Risk Scoring**: Assess threats on a 0–100 scale with granular severity levels.
- **Explainable AI (XAI)**: Generates human-readable justifications and local feature importance via **SHAP** for heuristic and ML flags.
- **Adaptive Learning**: Automated retraining scheduler that updates models based on live user feedback, persisted via a central **SQLAlchemy ORM**.

### Operations & Scalability

- **Docker Orchestration**: Production-ready multi-container setup (API + Scheduler + Database) managed by `docker-compose` with loopback database isolation (`127.0.0.1`).
- **Database Migrations**: Automated schema versioning via **Alembic** mapped to PostgreSQL/SQLite via SQLAlchemy.
- **Background Processing**: Heavy computational tasks and external alerts are offloaded to **ARQ** (Redis-based async queue).
- **Observability & Security Audit Logging**: Exposes a `/metrics` endpoint for **Prometheus** / Grafana, and logs structured security events to `logs/security_audit.log`.
- **Gmail Integration**: Automated inbox scanning using secure Google OAuth2 flows. [Read the Integration Guide](docs/GMAIL_INTEGRATION.md).

---

## Documentation Index

Explore our comprehensive documentation suite:

- 📖 [API Documentation](docs/API_DOCUMENTATION.md) — Complete endpoint reference, auth schemas, rate limits, and error codes.
- 🏗️ [System Architecture](docs/ARCHITECTURE.md) — Deep-dive into component design, pipelines, and data flow.
- 🛡️ [Input Validation & Sanitization Guide](docs/INPUT_VALIDATION_AND_SANITIZATION.md) — Reference on XSS escaping, null-byte stripping, regex constraints, and Pydantic validators.
- 🔒 [Security Audit & Compliance](docs/SECURITY_AUDIT_AND_COMPLIANCE.md) — Enterprise security posture, audit logging format (`logs/security_audit.log`), and compliance policies.
- 🚀 [Enterprise Operations Guide](docs/ENTERPRISE_DEPLOYMENT.md) — HTTPS setup, Docker loopback isolation, secrets management, and disaster recovery.
- 💻 [Developer Guide](docs/developer_guide.md) — Setup, testing instructions (**95/95 tests passing**), and codebase structure.
- 🤖 [ML Training Guide](docs/ML_TRAINING_GUIDE.md) — Dataset generation, vectorizers, hyperparameter tuning, and ensemble training.
- 🚩 [Security Flags Reference](docs/SECURITY_FLAGS.md) — Explanation of all 10 forensic threat rules.
- 🛠️ [CLI Reference](docs/CLI_REFERENCE.md) — Usage instructions for `cli/manage.py`.
- ✉️ [Gmail Integration Guide](docs/GMAIL_INTEGRATION.md) — Step-by-step setup for Gmail OAuth2 scanning.
- 🤝 [Contributing Guidelines](docs/CONTRIBUTING.md) — Coding conventions, security guidelines, and PR workflow.

---

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/VIPHACKER100/PhishShield-Engine.git
cd PhishShield-Engine

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

### 2. Run the Development Server

```bash
# Start API server
python cli/manage.py serve --port 8000
```

Access the interactive dashboard at [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard).

### 3. Run Security & Unit Tests

```bash
python -m pytest tests/test_input_validation.py tests/test_secrets_audit.py tests/test_auth_unit.py tests/test_abuse_protection.py -v
```

> **95 / 95 tests passing** across all security test modules.

---

## Maintainer

**VIPHACKER100 (Aryan Ahirwar)**  
*Cybersecurity Researcher | AI Security Lead*  
*Last Updated: 2026-09-02*
