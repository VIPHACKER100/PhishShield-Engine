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

## 📈 2. Automated Model Lifecycle (MLOps)

The internal Machine Learning ecosystem governs its own drift, monitoring, and validation.

- **A/B Testing:** Multi-pipeline inference runs internally handled by `src/models/ab_testing.py` where traffic can dynamically split between Naive Bayes and SVM.
- **Retrain Daemon:** `scripts/retrain_scheduler.py` is cron-executable. It analyzes records in `data/feedback.db` and when a threshold of misclassifications is corrected by users, it natively initiates GridSearch and saves a new `.pkl` ensemble to `models/` without server downtime.
- **Drift Monitoring:** Asynchronous instances within `src/models/drift_monitor.py` ensure live data inference length doesn't radically outpace training vectors.
- **Deep Learning Architecture Base:** `src/models/deep_learning.py` scaffolds operations designed to intake `bert-base-uncased` Transformers when massive context capacity is required without interrupting Scikit-Learn pipelines.

---

## 📡 3. Analytics & Explainable AI (XAI)

For cybersecurity analysts reviewing inbound traffic spikes:

- `POST /export-report`: Compiles an immediately readable mapping merging all 9 active Forensic Rules (Homographs, Brand Spoofing, Embedded Scripting) alongside the Scikit-learn outputs.
- `GET /analytics`: Spits out exact testing tolerances against F1-Scores and training subsets from `metrics.json`.
- `logs/compliance.log` & `logs/incidents.log`: Aggregated structured JSON output to track anomalous server behaviors compliant with rigid logging (Phase 72).

---

## ⛓️ 4. Chaos Monkey & Production Load Testing

To ensure reliability scaling past standard 60-RPM environments limiters:

- We deploy `scripts/benchmark.py` which triggers `asyncio` parallel threading designed to rapidly bombard the `POST /predict/batch` endpoint.
- PhishShield-Engine handles up to 10,000 parallel multi-email bulk arrays utilizing Uvicorn multi-threading without freezing DB interactions.
- During severe instance failure, `scripts/restore_backup.py` pulls active Vectorizer, Models, and Model Registry configurations out of `/backups`.
