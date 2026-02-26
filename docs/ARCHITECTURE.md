# 🏗️ PhishShield-Engine Architecture

This document provides a high-level overview of the **PhishShield-Engine** system architecture, detailing how the various components—from text preprocessing and forensic scanning to ensemble machine learning and the API gateway—interact to classify and flag threats in real-time.

---

## 🗺️ High-Level System Diagram

At its core, PhishShield-Engine relies on a multi-stage pipeline where an incoming email passes through a **Pre-flight Filter**, a **Forensic Security Scan**, and an **Ensemble ML Inference** engine before a normalized output and explanation are generated.

```mermaid
graph TD
    A[Client App / Gmail Integration] -->|HTTP POST JSON| B(FastAPI Gateway)
    
    B --> C{Rate Limiter & Auth}
    C -- Valid --> D[Payload Validation & Sanitization]
    C -- Blocked --> E[429 / 401 Error]

    D --> F[Text Preprocessor]
    
    %% Twin pipelines
    F -->|Raw Text & Headers| G[Forensic Confidence Scanners]
    F -->|Cleaned Tokens| H[Machine Learning Pipeline]

    %% Scanners
    subgraph Forensics[Security Scanners]
        G1[Homograph Detection]
        G2[Brand Spoofing]
        G3[Header/SPF Verification]
        G4[URL Obfuscation]
        G --> G1 & G2 & G3 & G4
    end

    %% ML Engine
    subgraph Machine Learning[Ensemble Intelligence]
        H1(TF-IDF Vectorizer)
        H2(Naive Bayes)
        H3(Support Vector Machine - SVM)
        H4(Random Forest - RF)
        H --> H1
        H1 --> H2 & H3 & H4
        H2 & H3 & H4 --> H5(Soft Voting Classifier)
    end

    %% Aggregation
    Forensics --> I[Risk Aggregator & Scoring]
    Machine Learning --> I
    
    %% Output
    I --> J{Threat Explanation Gen (XAI)}
    J --> K[Final Risk Object]
    
    %% Logging & Storage
    K --> L[(Threat Logging DB)]
    K -->|Actionable Response| A
```

---

## ⚙️ Core Components Description

### 1. API Interface & Traffic Routing (`src/api/`)

- **FastAPI Framework**: Serves as the high-throughput asynchronous gateway. By default, it runs on standard Uvicorn workers that manage connection pooling.
- **Middleware Security**: Intercepts requests to append distinct request IDs (`X-Request-ID`) and implements in-memory, per-IP rate limiting (60 RPM).
- **Authentication (`auth.py`)**: Uses Python's built-in `bcrypt` and `PyJWT` libraries. If user registration is enabled, all requests MUST contain a Bearer Auth token. Otherwise, an `X-API-Key` fallback can be accepted.

### 2. Preprocessing & Normalization (`src/preprocessing/`)

- **Text Cleaner**: Every raw email is stripped of HTML entity encoding, normalized to UTF-8 lowercase, and stripped of extraneous newline characters. Punctuation removal and NLTK-based stopword removal occur prior to term-frequency matrix rendering.
- **Anonymizer**: All PII (Personally Identifiable Information), including specific names and CC-ed email addresses, is dynamically replaced with regex placeholders before the string hits the threat storage or feedback loops.

### 3. Forensic Security Scanning (`src/security/`)

This is the deterministic, rules-based engine that acts adjacent to the ML predictors.

- **Homograph Protection**: Checks string buffers against the Latin, Cyrillic, and Greek unicode pools. Flags if a character looks like a standard Latin `A` but resolves to a Cyrillic character visually hiding a malicious domain.
- **URL & Zero-width Obfuscation**: Scans for embedded zero-width joiners (`\u200D` or `\u200B`) that attackers insert into body text to bypass spam-filters looking for common keywords.
- **Brand Intelligence**: Conducts aggressive fuzzy-matching on specific protected brand lists (e.g., Apple, PayPal). Calculates the Levenshtein distance against known safe domains.

### 4. Machine Learning & XAI (`src/models/`, `src/features/`)

- **Ensemble Structure**: Operates a `scikit-learn` stack combining MNB (Multinomial Naive Bayes, highly performant on NLP arrays), SVM (Support Vector Machines for complex non-linear boundary separation), and RF (Random Forests to smooth out outliers).
- **Continuous Tuning (`retrain_scheduler.py`)**: A daemon checks the `feedback.db` for new records. If a statistically significant threshold of end-user feedback is met, it runs grid search hyperparameter tuning locally, evaluates the new `F1` score, and promotes it to production if it beats the legacy model.

### 5. Config Governance (`config/config.yaml`)

Risk thresholds, model tuning grid-search parameters, security flag weights, and compliance retention windows are completely decoupled from runtime code. They are fetched from `config.yaml` using the built-in `config_loader` upon app boot.
