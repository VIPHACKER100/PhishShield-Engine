# PhishShield-Engine: API Documentation

Welcome to the **PhishShield-Engine** API reference. This platform provides a suite of RESTful endpoints for email security, phishing intelligence, and model management.

---

## Authentication & Identity

Users must register and login to receive a **JSON Web Token (JWT)**, which must be provided in the `Authorization` header for all protected endpoints.

### 1. User Registration

- **URL**: `/auth/register`
- **Method**: `POST`
- **Payload**: `{ "username": "...", "password": "..." }`

### 2. User Login

- **URL**: `/auth/login`
- **Method**: `POST`
- **Payload**: `{ "username": "...", "password": "..." }`
- **Response**: `{ "token": "...", "username": "..." }`

---

## Core Security Endpoints

### 3. Unified Prediction

Calculates both ML probability and Heuristic security risk.

- **URL**: `/predict`
- **Method**: `POST`
- **Payload**:

```json
{
  "text": "Your account has been compromised. Log in here: http://192.168.1.1",
  "headers": "From: amazon-security@attacker.com\nReturn-Path: evil@hacker.io",
  "model": "ensemble"
}
```

### 4. Detailed Security Analysis

Phase 49: Deep forensic analysis without ML overhead.

- **URL**: `/analyze-security`
- **Method**: `POST`
- **Payload**: `{ "text": "...", "headers": "..." }`
- **Response**: Detailed JSON including `risk_score`, `risk_level`, and specific `security_flags` (10 flags including `cyrillic_url`).

### 5. Batch Analysis

Process up to 100 emails in a single request.

- **URL**: `/predict/batch`
- **Method**: `POST`
- **Payload**: `{ "emails": ["text1", "text2"...], "model_name": "svm" }`

---

## Intelligence & Reporting

### 6. Analytics

Retrieve current performance metrics for all registered models.

- **URL**: `/analytics`
- **Method**: `GET`

### 7. Feedback Loop

Submit ground-truth corrections to trigger automated retraining. Feedback is stored in both `data/feedback/feedback_data.csv` and `data/feedback.db` (SQLite).

- **URL**: `/feedback`
- **Method**: `POST`
- **Payload**:

```json
{
  "email_text": "...",
  "predicted_label": "ham",
  "correct_label": "spam",
  "model_used": "naive_bayes"
}
```

### 8. Export Security Report
Phase 63: Forensic Analysis Export. Provides a complete, downloadable forensic breakdown of an email's threat indicators.

- **URL**: `/export-report`
- **Method**: `POST`
- **Payload**: `{ "text": "...", "headers": "..." }`
- **Response**: Full JSON forensic mapping containing timestamps, extracted URLs, and risk breakdown.

### 9. A/B Testing Analytics

Returns the real-time split testing summary for active models.

- **URL**: `/ab/summary`
- **Method**: `GET`
- **Response**: `{ "naive_bayes": {"count": 10}, "svm": {"count": 12} }`

---

## Utility Endpoints

### 10. Health Checks & Observability

- `GET /health`: Core system status.
- `GET /health/ready`: Checks model readiness and DB connections.
- `GET /metrics`: **Prometheus** metrics endpoint exposing active instrumentations (request counts, latency histograms).

### 11. Interactive Documentation

- `GET /docs`: Swagger UI for interactive testing.
- `GET /redoc`: ReDoc clean documentation view.

---
**Last Updated**: 2026-06-23
