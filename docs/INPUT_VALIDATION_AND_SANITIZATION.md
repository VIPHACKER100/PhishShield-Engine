# PhishShield-Engine: Input Validation & Sanitization Security Reference

## Overview

The **PhishShield-Engine** platform enforces defense-in-depth input validation, text sanitization, and input type constraints across all API endpoints, request schemas, database operations, and command-line interfaces (CLI).

---

## 1. Central Input Sanitizer Utility (`src/utils/sanitizer.py`)

All raw input entering the system passes through centralized validation and sanitization functions:

### Key Functions & Enforcement Rules

| Function | Validation / Sanitization Rule | Target Threat / Protection |
|---|---|---|
| `sanitize_text()` | Strips null bytes (`\0`), removes non-printable ASCII control characters (`\x00-\x08\x0b\x0c\x0e-\x1f\x7f`), HTML-escapes script tags (`<script>`, `<iframe>`, `javascript:`) via `html.escape`, and truncates to `max_length`. | Prevents Stored/Reflected XSS, HTML injection, null-byte truncation attacks, and buffer bloat. |
| `validate_username()` | Enforces regex `^[a-zA-Z0-9_-]{3,50}$`. Rejects spaces, quotes, control characters, and SQL injection syntax (`admin' OR 1=1--`). | Prevents SQL injection, command injection, and username-based XSS attacks. |
| `validate_domain()` | Enforces FQDN domain regex `^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$`. Converts domains to lowercase. | Prevents bad data insertion and SQL formatting errors in threat intelligence DB. |
| `validate_token()` | Enforces URL-safe token regex `^[a-zA-Z0-9._-]{1,128}$`. | Prevents token tampering and malformed key injection. |
| `validate_model_name()` | Whitelist validation: `naive_bayes`, `svm`, `ensemble`, `transformers`, `deep_learning`. | Prevents model path traversal and arbitrary execution. |
| `validate_label()` | Whitelist validation: `spam` or `ham`. | Prevents classification label manipulation. |

---

## 2. Request Schema Integration (`src/api/schemas.py`)

Every API endpoint validates incoming JSON bodies using **Pydantic `@field_validator`** hooks:

### Schema Validation Summary

- **`PredictRequest`**:
  - `text`: `sanitize_text(v, max_length=50_000)` (strips null bytes, escapes HTML tags).
  - `headers`: `sanitize_text(v, max_length=10_000)`.
  - `model`: `validate_model_name(v)` (whitelist check).
  - `bot_trap`: Honeypot field — populated values trigger instant HTTP 422 rejection.

- **`BatchPredictRequest`**:
  - `emails`: `max_length=50` items. Each email text sanitized via `sanitize_text(v, max_length=50_000)`.
  - `model_name`: `validate_model_name(v)`.

- **`RegisterRequest`**:
  - `username`: `validate_username(v)` (`^[a-zA-Z0-9_-]{3,50}$`).
  - `password`: `min_length=8, max_length=128`. Capped at 128 characters to prevent **bcrypt CPU Denial-of-Service** attacks.
  - `email`: Validates email structure; rejects control characters (`\n`, `\r`, `\0`) to prevent **HTTP header injection** or **SMTP split attacks**.
  - `bot_trap`: Honeypot field.

- **`LoginRequest`**:
  - `username`: `validate_username(v)`.
  - `password`: `max_length=128`.

- **`PasswordResetSchema`**:
  - `username`: `validate_username(v)`.
  - `token`: `validate_token(v)` (`^[a-zA-Z0-9._-]{1,128}$`).
  - `new_password`: `min_length=8, max_length=128`.

- **`FeedbackRequest`**:
  - `email_text`: `sanitize_text(v)`.
  - `predicted_label` & `correct_label`: `validate_label(v)` (`spam` | `ham`).
  - `model_used`: `validate_model_name(v)`.

---

## 3. Database Parameterization & CLI Validation

### Parameterized SQL Queries
Database queries across `SQLAlchemy ORM` (`src/core/database.py`) and SQLite (`src/security/threat_intel.py`) use **strictly parameterized inputs**:

```python
# Safe SQLite query in src/security/threat_intel.py
c.execute("SELECT reason FROM bad_domains WHERE domain = ?", (clean_domain,))
```

### CLI Command Input Validation (`cli/manage.py`)
CLI inputs run through domain format validation (`validate_domain()`) and text sanitization before modifying threat intelligence storage:

```bash
# Valid command
python cli/manage.py block evil-phish.com --reason "Credential harvesting"

# Invalid command (rejected by validate_domain with clear error message)
python cli/manage.py block "invalid domain spaces"
```

---

## 4. Test Suite & Verification

The validation suite is verified via `tests/test_input_validation.py` (**29 / 29 tests passing**):

```bash
python -m pytest tests/test_input_validation.py -v
```

Covered scenarios:
- HTML/XSS script tag escaping (`<script>alert(1)</script>`).
- Null byte stripping (`\x00`).
- SQL injection attempt rejection in usernames (`admin' OR 1=1--`).
- Email newline/header injection rejection (`\r\nBcc: evil@hacker.io`).
- Model name and label whitelist enforcement.
- Domain syntax validation.

---

**Maintainer**: VIPHACKER100 (Aryan Ahirwar)  
**Last Updated**: 2026-09-02
