# 📡 PhishShield-Engine: API Documentation

Welcome to the **PhishShield-Engine** API reference. This platform provides a suite of RESTful endpoints for email security, phishing intelligence, and model management.

---

## 🔐 Authentication

Most endpoints require a **JSON Web Token (JWT)** in the `Authorization` header.

```http
Authorization: Bearer <your_jwt_token>
```

---

## 📧 Core Security Endpoints

### 1. Unified Prediction

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

- **Response**:

```json
{
  "prediction": "spam",
  "probability": 0.98,
  "security_risk_score": 85,
  "risk_level": "HIGH RISK",
  "threat_reasons": ["Header Spoof", "IP link detected"],
  "security_flags": { "obfuscation": false, "homograph": false ... }
}
```

### 2. Batch Analysis

Process up to 100 emails in a single request.

- **URL**: `/predict/batch`
- **Method**: `POST`
- **Payload**: `{ "emails": ["text1", "text2"...], "model_name": "svm" }`

---

## ⛓️ Threat Intelligence Endpoints

### 3. Domain Blocklist

Add a domain to the local threat database.

- **URL**: `/intel/block`
- **Method**: `POST`
- **Payload**: `{ "domain": "malicious.org", "reason": "Phishing" }`

### 4. Intel Lookup

Check if a domain is known to the intelligence engine.

- **URL**: `/intel/check/{domain}`
- **Method**: `GET`

---

## 🧠 Model Management

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

---

## 🛠️ Utility Endpoints

### 7. Health Checks

- `GET /health`: Core system status.
- `GET /health/ready`: Checks model readiness and DB connections.

### 8. Interactive Documentation

- `GET /docs`: Swagger UI for interactive testing.
- `GET /redoc`: ReDoc clean documentation view.
