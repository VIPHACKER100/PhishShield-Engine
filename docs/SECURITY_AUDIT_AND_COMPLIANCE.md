# PhishShield-Engine: Security Audit & Compliance Architecture

## Executive Summary

**PhishShield-Engine** maintains a zero-trust, enterprise-ready security architecture. This document defines the security posture, structured audit logging standards (`logs/security_audit.log`), data retention compliance (`logs/compliance.log`), access control controls, and verification test metrics.

---

## 1. Security Architecture & Controls Matrix

| Security Layer | Implementation Details | Target Vulnerability / Threat |
|---|---|---|
| **Password Hashing** | `bcrypt` work-factor salting with 8+ char complexity (digit + special char) | Plaintext credential exposure, weak passwords |
| **Bcrypt DoS Protection** | 128-character limit on all password inputs | CPU exhaustion via ultra-long password strings |
| **Session Security** | Short-lived JWTs (1 hour), `jti` & `iat` claims, HS256 signature | Session hijacking, replay attacks |
| **Account Lockout** | Account locked 15 minutes after 5 consecutive failed logins (`locked_until`) | Brute-force dictionary attacks |
| **Enumeration Protection** | Constant-time dummy `bcrypt` checks on unknown users; generic 401 response | User enumeration, timing attacks |
| **API Key Comparison** | `hmac.compare_digest()` for `pse_` API keys | Timing side-channel attacks |
| **IDOR Defense** | Ownership checks `resource.user_id == current_user.id` on all resource routes | Insecure Direct Object References |
| **Rate Limiting** | SlowAPI per-endpoint limits (`5/min` login, `15/min` predict, `5/min` batch) | API abuse, Denial of Service |
| **Anti-Bot Protection** | Empty User-Agent block, 14-tool scanner blacklist (`sqlmap`, `nikto`), honeypot traps | Automated scraping, automated exploit scanning |
| **Deployment Security** | HSTS, CSP, X-Frame-Options, `127.0.0.1` loopback PostgreSQL/Redis bindings | Public database exposure, Clickjacking, XSS |
| **Input Sanitization** | Null-byte stripping, HTML escaping, strict regex for username/domain/token | Stored/Reflected XSS, SQL injection |
| **Zero-Trust Secrets** | Environment-first vault, `ENV=prod` startup guard refusing default keys | Hardcoded secrets, credential leaks |

---

## 2. Structured Security Audit Log Standard (`logs/security_audit.log`)

Security audit events are written to `logs/security_audit.log` via `security_logger` (`src/utils/logger.py`) using rotating file handlers (10MB, 10 backups).

### Log Format
`[TIMESTAMP] [LEVEL] [SECURITY] EVENT=<type> IP=<ip> USER=<user> DETAIL=<detail>`

### Event Directory

| Event Name | Trigger Condition | Severity |
|---|---|---|
| `SYSTEM_STARTUP` | Application process initialization | INFO |
| `USER_REGISTERED` | Successful user creation | INFO |
| `AUTH_SUCCESS` | Successful login authentication | INFO |
| `AUTH_FAILURE` | Failed login attempt (wrong password or nonexistent user) | WARNING |
| `ACCOUNT_LOCKED` | Account locked due to 5 consecutive failures | WARNING |
| `PASSWORD_RESET_REQUESTED` | Password reset token generated | INFO |
| `PASSWORD_RESET_SUCCESS` | Password changed via reset token | INFO |
| `RATE_LIMIT_EXCEEDED` | Client exceeded endpoint rate limit threshold | WARNING |
| `BOT_ATTACK_BLOCKED` | Request from blacklisted scanner User-Agent | WARNING |
| `BOT_BLOCKED_EMPTY_UA` | Request to API endpoint without User-Agent header | WARNING |
| `BOT_HONEYPOT_TRIGGERED` | Request containing `X-Honeypot-Trap` or `X-Bot-Check` header | WARNING |
| `CLIENT_ERROR` | HTTP 4xx response anomaly (400, 401, 403, 404, 422) | INFO / WARNING |
| `SERVER_ERROR` | HTTP 5xx response anomaly | ERROR |

---

## 3. Compliance & Data Retention (`logs/compliance.log`)

PhishShield enforces automated compliance retention governed by `config/config.yaml` (`auto_retention_days: 30`).

- Data retention policies and forensic overrides log to `logs/compliance.log` via `src/utils/compliance.py`.
- Anonymization pipeline (`src/utils/anonymizer.py`) automatically strips PII (email addresses, phone numbers, SSNs, credit cards) from email text before saving feedback entries.

---

## 4. Verification Test Metrics

Security mechanisms are validated by an automated test suite (**95 / 95 tests passing**):

```bash
# Execute full security test suite
python -m pytest tests/test_input_validation.py tests/test_secrets_audit.py tests/test_auth_unit.py tests/test_abuse_protection.py -v
```

### Test Breakdown

- `tests/test_input_validation.py`: 29 tests (XSS, null bytes, regex username/domain/token, schema validators)
- `tests/test_secrets_audit.py`: 16 tests (env priority, prod startup guard, gitignore rules, Kafka config)
- `tests/test_auth_unit.py`: 21 tests (bcrypt hashing, JWT lifetime, account lockout, IDOR protection)
- `tests/test_abuse_protection.py`: 29 tests (rate limits, bot User-Agent blacklist, honeypot traps)

---

**Maintainer**: VIPHACKER100 (Aryan Ahirwar)  
**Last Updated**: 2026-09-02
