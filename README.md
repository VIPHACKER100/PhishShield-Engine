# 🛡️ PhishShield-Engine

**PhishShield-Engine** is an AI-powered email security platform designed to detect spam, phishing attacks, malicious URLs, homograph spoofing, and identity impersonation using advanced machine learning and multi-layer forensic intelligence.

---

## 🚀 GitHub Repository

```text
PhishShield-Engine
```

---

## 🧠 Short Description

AI-powered email security engine that identifies spam, phishing, and identity spoofing using ensemble machine learning and advanced cybersecurity heuristics.

> **“Smart AI defense for your inbox.”**

---

## 🔥 Key Technical Features

### �️ Core Security Intelligence

- **Phishing Detection**: Specialized logic for identifying social engineering and credential theft attempts.
- **Obfuscation Defense (Phase 85)**: Advanced detection of zero-width characters and hidden markers used to bypass traditional filters.
- **Homograph Attack Protection**: Identifies IDN (Internationalized Domain Name) attacks and Unicode-based visual spoofing.
- **Fuzzy Brand Protection**: Detects impersonation of 15+ major global brands (PayPal, Amazon, Google, etc.).
- **Header Forensics**: Deep validation of SPF/DKIM/DMARC and detection of sender-domain mismatches.

### 🧠 Machine Learning Engine

- **Ensemble Intelligence**: High-performance voting classifier combining Naive Bayes, SVM, and Random Forests.
- **Quantitative Risk Scoring**: Assess threats on a 0–100 scale with granular severity levels.
- **Explainable AI (XAI)**: Generates human-readable justifications for every heuristic security flag.
- **Adaptive Learning**: Automated retraining scheduler that updates models based on live user feedback.

### ⚙️ Operations & Scalability

- **Docker Orchestration (Phase 81)**: Production-ready multi-container setup (API + Scheduler + Database).
- **Gmail Integration (Phase 83)**: Automated inbox scanning using secure Google OAuth2 flows. [Read the Integration Guide](docs/GMAIL_INTEGRATION.md).
- **Developer CLI**: Productivity tool for managing local blocklists, monitoring metrics, and launching the platform.
- **YAML Governance**: Centralized configuration for security weights, risk thresholds, and compliance policies.

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate    # macOS/Linux

# Install the engine as a package
pip install -e .
```

### 2. Model Initialization

```bash
# Generate synthetic dataset and train the ensemble pipeline
python scripts/train_pipeline.py --generate --ensemble
```

### 3. Launch the Platform

```bash
python cli/manage.py serve
```

Open [http://localhost:8000](http://localhost:8000) for the Interactive Security Dashboard.

---

## 📂 Project Structure

```text
PhishShield-Engine/
├── .github/                   # CI/CD Workflows (GitHub Actions)
├── cli/                       # Developer Management Tool (manage.py)
├── config/                    # Global Governance (config.yaml)
├── data/                      # Persistent Threat Intelligence, Databases & Feedback
├── docs/                      # Technical Documentation (API & Developer Guide)
├── models/                    # Trained Model Artifacts (.pkl) & Metrics
├── scripts/                   # Retraining, Chaos Monkey & Pipeline Automation
├── src/                       # Source Code
│   ├── api/                   # FastAPI Server & Cinematic UI
│   ├── features/              # Feature Engineering & Vectorization
│   ├── integrations/          # Gmail API Scanning Client
│   ├── models/                # ML Inference, Training, Evaluating & XAI
│   ├── preprocessing/         # Text Cleaning & Normalization
│   ├── security/              # Forensic Engines (URL, Homograph, Brand, Obfuscation)
│   └── utils/                 # Config Loader, Logger & Compliance Tools
├── tests/                     # Unit & Integration Testing Suite (pytest)
├── docker-compose.yml         # Container Orchestration
├── Dockerfile                 # Docker Image Generation
├── requirements.txt           # Python Dependencies
└── README.md
```

---

## 👨‍💻 Author

**VIPHACKER100 (Aryan Ahirwar)**
Cybersecurity Researcher | AI Security Developer
*Last Updated: 2026-04-03*

---

## ⚖️ License & Disclaimer

This tool is for educational and defensive security purposes only. Licensed under MIT.

---

## 📖 Documentation

Detailed technical documentation is available in the `docs/` directory:

- [System Architecture](docs/ARCHITECTURE.md): High-level system design diagram, data flow, and modular components.
- [Security Flags Guide](docs/SECURITY_FLAGS.md): In-depth breakdown of the **9 independent forensic threat scanners**.
- [Developer Guide](docs/developer_guide.md): Code structure, CLI setup, and automated maintenance procedures.
- [API Documentation](docs/API_DOCUMENTATION.md): Complete REST endpoint reference (Auth, Prediction, Reporting).
- [Gmail Integration](docs/GMAIL_INTEGRATION.md): Guide to configuring Google OAuth2 for automated inbox scanning.
- [Enterprise Deployment](docs/ENTERPRISE_DEPLOYMENT.md): MLOps, scalability, zero-trust secrets, and disaster recovery.
- [CLI Reference](docs/CLI_REFERENCE.md): Command-line toolkit guide for `manage.py` and automation scripts.
- [ML Training Guide](docs/ML_TRAINING_GUIDE.md): End-to-end model lifecycle, vectorization, and ensemble tuning.

---

## ⭐ Contribute

Contributions are highly welcome! Please read our [Contributing Guidelines](docs/CONTRIBUTING.md) to log setup PRs and get started.

If this project helps you, please consider giving it a star!
