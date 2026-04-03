# 📡 PhishShield-Engine: API Documentation

Welcome to the **PhishShield-Engine** API reference. This platform provides a suite of RESTful endpoints for email security, phishing intelligence, and model management.

---

## 🔐 Authentication & Identity

Users must register and login to receive a **JSON Web Token (JWT)**, which must be provided in the `Authorization` header for all protected endpoints.

### 1. User Registration

- **URL**: `/auth/register`
- **Method**: `POST`
- **Payload**: `{ "username": "...", "password": "..." }`

### 2. User Login

- **URL**: `/auth/login`
- **Method**: `POST`
- **Payload**: `{ "username": "...", "password": "..." }`
- **Response**: `{ "access_token": "...", "token_type": "bearer" }`

---

## 📧 Core Security Endpoints

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
- **Response**: Detailed JSON including `risk_score`, `risk_level`, and specific `security_flags`.

### 5. Batch Analysis

Process up to 100 emails in a single request.

- **URL**: `/predict/batch`
- **Method**: `POST`
- **Payload**: `{ "emails": ["text1", "text2"...], "model_name": "svm" }`

---

## 📊 Intelligence & Reporting

### 5. Analytics

Retrieve current performance metrics for all registered models.

- **URL**: `/analytics`
- **Method**: `GET`

### 6. Feedback Loop

Submit ground-truth corrections to trigger automated retraining.

- **URL**: `/feedback`
- **Method**: `POST`
- **Payload**:

```json
{
  "text": "...",
  "predicted_label": "ham",
  "correct_label": "spam"
}
```

### 7. Export Security Report
Phase 63: Forensic Analysis Export. Provides a complete, downloadable forensic breakdown of an email's threat indicators.

- **URL**: `/export-report`
- **Method**: `POST`
- **Payload**: `{ "text": "...", "headers": "..." }`
- **Response**: Full JSON forensic mapping containing timestamps, extracted URLs, and risk breakdown.

### 8. A/B Testing Analytics

Returns the real-time split testing summary for active models.

- **URL**: `/ab/summary`
- **Method**: `GET`
- **Response**: `{ "naive_bayes": {"count": 10}, "svm": {"count": 12} }`

---

## 🛠️ Utility Endpoints

### 9. Health Checks

- `GET /health`: Core system status.
- `GET /health/ready`: Checks model readiness and DB connections.

### 10. Interactive Documentation

- `GET /docs`: Swagger UI for interactive testing.
- `GET /redoc`: ReDoc clean documentation view.
