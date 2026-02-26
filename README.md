# 🛡️ PhishShield-Engine

**PhishShield-Engine** is an AI-powered email security platform designed to detect spam, phishing attacks, malicious URLs, homograph spoofing, and identity impersonation using advanced machine learning and multi-layer forensic intelligence.

---

## 🚀 GitHub Repository

```
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
- **Gmail Integration (Phase 83)**: Automated inbox scanning and threat response using secure Google OAuth2 flows.
- **Developer CLI**: Productivity tool for managing local blocklists, monitoring metrics, and launching the platform.
- **YAML Governance**: Centralized configuration for security weights, risk thresholds, and compliance policies.

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
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

```
PhishShield-Engine/
├── src/
│   ├── api/                   # FastAPI server & Cinematic UI
│   ├── security/              # Forensic Engines (URL, Homograph, Brand, Obfuscation)
│   ├── models/                # ML Inference, Training & XAI
│   ├── integrations/          # Gmail API Scanning Client
│   └── utils/                 # Config Loader & Compliance Tools
├── cli/                       # Developer Management Tool (manage.py)
├── config/                    # Global Governance (config.yaml)
├── data/                      # Persistent Threat Intelligence & Feedback
├── models/                    # Trained Model Artifacts (.pkl)
├── scripts/                   # Retraining, Chaos Monkey & Automation
└── README.md
```

---

## 👨‍💻 Author

**VIPHACKER100 (Aryan Ahirwar)**
Cybersecurity Researcher | AI Security Developer

---

## ⚖️ License & Disclaimer

This tool is for educational and defensive security purposes only. Licensed under MIT.

---

## 📖 Documentation

Detailed technical documentation is available in the `docs/` directory:

- [Developer Guide](docs/developer_guide.md): Architecture, setup, and contribution workflows.
- [API Documentation](docs/API_DOCUMENTATION.md): Complete REST endpoint reference.

---

## ⭐ Contribute

Contributions are welcome! Please open an issue or submit a pull request to help improve email security for everyone.
