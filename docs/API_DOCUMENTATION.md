# PhishShield-Engine: API Documentation

Welcome to the **PhishShield-Engine** API reference. This platform provides a suite of RESTful endpoints for email security, phishing intelligence, and model management.

---

## Authentication & Identity

Users must register and login to receive a **JSON Web Token (JWT)**, which must be provided in the `Authorization` header for all protected endpoints.

### Security Controls

| Control | Detail |
|---------|--------|
| Password hashing | bcrypt with auto work-factor (`gensalt()`) |
| JWT lifetime | **1 hour** (configurable via `JWT_EXPIRY_HOURS`) |
| JWT claims | `sub`, `iat`, `exp`, `jti` (unique ID per token) |
| Account lockout | After **5** consecutive failures, locked for **15 minutes** |
| Rate limit — login | **5 requests / minute** per IP |
| Rate limit — register | **3 requests / minute** per IP |
| Rate limit — reset | **3 requests / minute** per IP |
| User enumeration | All auth failure responses are identical — no distinction between "wrong password" and "no such user" |
| API key comparison | Constant-time via `hmac.compare_digest()` — no timing oracle |

---

### 1. User Registration

- **URL**: `POST /auth/register`
- **Rate limit**: 3 / minute per IP
- **Payload**:

```json
{
  "username": "alice",
  "password": "Secure@Pass1!",
  "email": "alice@example.com"
}
```

**Password policy** (enforced server-side):
- Minimum **8 characters**
- At least **one digit**
- At least **one special character** (`!@#$%^&*` etc.)

**Response** (`200 OK`):

```json
{
  "username": "alice",
  "api_key": "pse_<48-char hex>"
}
```

> ⚠️ The `api_key` is returned **once only** at registration. Store it securely — it cannot be retrieved again.

---

### 2. User Login

- **URL**: `POST /auth/login`
- **Rate limit**: 5 / minute per IP
- **Payload**:

```json
{ "username": "alice", "password": "Secure@Pass1!" }
```

- **Response** (`200 OK`):

```json
{
  "token": "<JWT>",
  "username": "alice",
  "expires_in": 3600
}
```

- **Failure** (`401 Unauthorized`): Returns `"Invalid credentials"` for wrong password, unknown user, **or** locked account — no distinction is made.

---

### 3. Password Reset — Request Token

- **URL**: `POST /auth/password-reset-request`
- **Rate limit**: 3 / minute per IP
- **Payload**: `{ "username": "alice" }`
- **Response** (`200 OK`, always — even if username does not exist):

```json
{
  "detail": "If that username exists, a password-reset token has been issued.",
  "_dev_token": "<raw token>"
}
```

> ⚠️ `_dev_token` is present in development mode only. In production, remove this field and deliver the token via email out-of-band.

Token properties:
- Generated with `secrets.token_urlsafe(32)` (256-bit entropy)
- Valid for **1 hour** (configurable via `RESET_TOKEN_EXPIRY_HOURS`)
- SHA-256 hash stored in DB — raw token is never persisted
- **Single-use**: invalidated immediately after first successful `password-reset`

---

### 4. Password Reset — Consume Token

- **URL**: `POST /auth/password-reset`
- **Rate limit**: 5 / minute per IP
- **Payload**:

```json
{
  "username": "alice",
  "token": "<raw token from email>",
  "new_password": "NewSecure@Pass2!"
}
```

- **Response** (`200 OK`): `{ "detail": "Password updated successfully." }`
- **Failure** (`400`): `{ "detail": "Invalid or expired reset token." }`

---

### 5. User Profile & Owned Resource Access (IDOR Protected)

The following endpoints allow authenticated users to view and manage their own resources. Every query strictly verifies that `resource.user_id == current_user.id`. Access attempts on another user's resources return `404 Not Found` (preventing IDOR attacks).

#### Profile Info
- **URL**: `GET /auth/me`
- **Auth**: Required (`Bearer <JWT>` or `X-API-Key`)
- **Response** (`200 OK`):
  ```json
  {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "is_email_verified": false,
    "created_at": "2026-09-02T18:00:00+00:00"
  }
  ```

#### Usage Logs (Owned)
- **URL**: `GET /auth/logs`
- **Auth**: Required (`Bearer <JWT>` or `X-API-Key`)
- **Response** (`200 OK`): List of usage log entries belonging to the authenticated user.

#### Specific Usage Log (IDOR Protected)
- **URL**: `GET /auth/logs/{log_id}`
- **Auth**: Required (`Bearer <JWT>` or `X-API-Key`)
- **Response**: `200 OK` if owned by user; `404 Not Found` if not owned or missing.

#### Specific Feedback Entry (IDOR Protected)
- **URL**: `GET /auth/feedback/{feedback_id}`
- **Auth**: Required (`Bearer <JWT>` or `X-API-Key`)
- **Response**: `200 OK` if owned by user; `404 Not Found` if not owned or missing.

#### Delete Feedback Entry (IDOR Protected)
- **URL**: `DELETE /auth/feedback/{feedback_id}`
- **Auth**: Required (`Bearer <JWT>` or `X-API-Key`)
- **Response**: `200 OK` if owned by user; `404 Not Found` if not owned or missing.

---

### Authentication Headers

For protected endpoints, provide credentials using **one** of:

```
Authorization: Bearer <JWT token>
X-API-Key: pse_<api key>
```

---

## Core Security Endpoints

### 5. Unified Prediction

Calculates both ML probability and heuristic security risk.

- **URL**: `POST /predict`
- **Payload**:

```json
{
  "text": "Your account has been compromised. Log in here: http://192.168.1.1",
  "headers": "From: amazon-security@attacker.com\nReturn-Path: evil@hacker.io",
  "model": "ensemble"
}
```

### 6. Detailed Security Analysis

Deep forensic analysis without ML overhead.

- **URL**: `POST /analyze-security`
- **Payload**: `{ "text": "...", "headers": "..." }`
- **Response**: Detailed JSON including `risk_score`, `risk_level`, and specific `security_flags` (10 flags).

### 7. Batch Analysis

Process up to 100 emails in a single request.

- **URL**: `POST /predict/batch`
- **Auth required**: Bearer token or X-API-Key
- **Payload**: `{ "emails": ["text1", "text2"...], "model_name": "svm" }`

---

## Intelligence & Reporting

### 8. Analytics

Retrieve current performance metrics for all registered models.

- **URL**: `GET /analytics`

### 9. Feedback Loop

Submit ground-truth corrections to trigger automated retraining.

- **URL**: `POST /feedback`
- **Payload**:

```json
{
  "email_text": "...",
  "predicted_label": "ham",
  "correct_label": "spam",
  "model_used": "naive_bayes"
}
```

### 10. Export Security Report

Full forensic breakdown of an email's threat indicators.

- **URL**: `POST /export-report`
- **Payload**: `{ "text": "...", "headers": "..." }`
- **Response**: Full JSON forensic mapping with timestamps, extracted URLs, and risk breakdown.

### 11. A/B Testing Analytics

- **URL**: `GET /ab/summary`
- **Response**: `{ "naive_bayes": {"count": 10}, "svm": {"count": 12} }`

---

## Utility Endpoints

### 12. Health Checks & Observability

- `GET /health` — Core system status.
- `GET /health/ready` — Checks model readiness and DB connections.
- `GET /metrics` — **Prometheus** metrics endpoint (request counts, latency histograms).

### 13. Interactive Documentation

- `GET /docs` — Swagger UI for interactive testing.
- `GET /redoc` — ReDoc clean documentation view.

---

## Error Reference

| HTTP Code | Meaning |
|-----------|---------|
| `401` | Invalid credentials, locked account, or expired/invalid token |
| `409` | Username or email already exists |
| `422` | Validation error (password policy, field length, etc.) |
| `429` | Rate limit exceeded — slow down requests |
| `400` | Invalid or expired password reset token |
| `503` | Models not yet trained / service not ready |

---

**Last Updated**: 2026-09-02
