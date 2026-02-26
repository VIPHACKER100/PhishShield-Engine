# 🛡️ PhishShield-Engine: Comprehensive Developer Guide

## 🎭 Overview

This document provides exhaustive documentation on the architecture, command-line interfaces, and maintenance procedures for the **PhishShield-Engine** platform.

---

## 🚀 Installation & Build

### 1. Local Environment Setup

```bash
# Initialize Virtual Environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install All Dependencies
pip install -r requirements.txt
```

### 2. Model Initialization

You must initialize your models before the first run:

```bash
# Generate 5,000 synthetic samples and train the high-performance Ensemble model
python scripts/train_pipeline.py --generate --n_samples 5000 --ensemble
```

---

## 🛠️ Command Reference

### I. The Management CLI (`manage.py`)

Used for day-to-day operations and threat intelligence management.

| Command | Arguments | Description |
|:---|:---|:---|
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
|:---|:---|:---|
| `--dataset_path` | `data/raw/emails.csv` | Path to the training dataset. |
| `--model_type` | `tfidf` | Vectorizer algorithm (`tfidf` or `bow`). |
| `--generate` | (False) | Generates high-fidelity synthetic phishing samples. |
| `--n_samples` | 1000 | Number of samples to generate if `--generate` is used. |
| `--tune` | (False) | Triggers GridSearchCV hyperparameter tuning. |
| `--ensemble` | (False) | Trains the triple-model VotingClassifier (NB/SVM/RF). |

### III. Operational Scripts

* **`python scripts/retrain_scheduler.py`**: Background daemon that monitors `data/feedback.db`. Triggers retraining once new feedback exceeds the threshold.
* **`python scripts/chaos_monkey.py`**: Injects faults (ML model corruption, load spikes) to verify graceful degradation.
* **`python scripts/backup.py backup`**: Creates a timestamped snapshot of models, threat DBs, and configs.

---

## 🛡️ Security Core Architecture

### 1. Forensic Intelligence Layer

The `calculate_security_risk` function (in `src/security/risk_scoring.py`) executes 8 independent forensic scans:

* **Obfuscation Scan**: Detects zero-width icons/markers via `src/security/obfuscation_detector.py`.
* **Homograph Scan**: Identifies "lookalike" Unicode domains (punycode detection).
* **Brand Protection**: Fuzzy-matches against 15+ high-value target brands.
* **Header Forensics**: SPF/DKIM/DMARC validation and `Return-Path` analysis.
* **Domain Intel**: Local SQLite lookup of known malicious domains.

### 2. Governance-as-Code (`config/config.yaml`)

Control the engine's behavior without modifying code:

* **Weights**: Adjust the risk contribution of each forensic flag.
* **Thresholds**: Define "High Risk" and "Suspicious" cutoffs.
* **Compliance**: Define auto-retention days (Default: 30 days).

---

## ☁️ Production Orchestration (Docker)

The platform is designed to run as a multi-service architecture using **Docker Compose**:

```bash
# Launch API, Threat DB, and Retraining Scheduler
docker-compose up --build -d
```

* **Service API**: Exposes the port `8000`.

* **Service Scheduler**: Runs the automated retraining watcher.
* **Persistence**: Volumes are mapped for `data/` and `logs/` to prevent loss during restarts.

---

## 🧪 Testing & Quality Assurance

* **Unit Tests**: `python -m pytest tests/`

* **Integration Tests**: `python scripts/chaos_monkey.py` (Simulates failure scenarios)
* **Compliance Audit**: View `logs/compliance.log` to audit data retention and forensic overrides.

---

## 🗺️ Implementation Roadmap (80 Phases)

The evolution of **PhishShield-Engine** followed a rigorous 80-phase roadmap, categorized into logical development layers.

### Phase 1–20: Core Infrastructure & Machine Learning

- **Fundamental NLP**: Implementation of TF-IDF and Bag-of-Words vectorizers.
* **Ensemble ML**: Training of Naive Bayes, SVM, and Random Forest classifiers.
* **REST Gateway**: Building the initial FastAPI structure and Pydantic models.
* **Cinematic UI**: Developing the glassmorphic frontend for user interaction.

### Phase 21–40: Security Foundations & Forensic Scanning

- **URL Intelligence**: Regex-based extraction and basic malicious pattern detection.
* **Homograph Defense**: Detecting IDN (Internationalized Domain Name) spoofing.
* **Mixed-Script Detection**: Identifying "lookalike" characters from Latin, Greek, and Cyrillic scripts.
* **Brand Protection (v1)**: Initial fuzzy-matching for top-tier brands like PayPal and Amazon.

### Phase 41–60: Advanced Phishing Intelligence

- **Header Forensics**: SPF, DKIM, and DMARC analysis for sender authenticity.
* **Risk Scoring Engine**: Implementation of the 0–100 weighted scoring system.
* **Explainable AI (XAI)**: Generation of human-readable justifications for security alerts.
* **Local Threat Hub**: SQLite-backed persistent database for domain blocklisting.

### Phase 61–75: Enterprise Governance & Operations

- **Configuration Management**: Centralized YAML-based settings for security weights.
* **Data Governance**: GDPR-ready retention policies and persistent audit logging.
* **Dockerization**: Containerizing the platform for environment parity and deployment.
* **Developer CLI**: Building the `manage.py` tool for operational productivity.

### Phase 76–80: Resilience, Automation & Final Production

- **Feedback Loop**: Implementing automated logic for model retraining based on live user data.
* **Chaos Engineering**: Stress-testing system resilience using failure injectors.
* **Production Verification**: Full-spectrum forensic testing and final brand alignment.
* **PhishShield Launch**: Rebranding and final stabilization of the production engine.

---

## 👨‍💻 Maintainer

**VIPHACKER100 (Aryan Ahirwar)**
*Cybersecurity Researcher | AI Security Lead*
