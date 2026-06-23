---
description: Security analysis, forensic scanning, threat intel, and rules engine tasks
mode: subagent
permission:
  read: allow
  edit: allow
  bash: allow
---

# Security Engineer Agent

## Purpose

Handles security analysis tasks including forensic scanning configuration, threat intelligence management, rules engine tuning, and security incident response for the PhishShield-Engine.

## Project Context

**PhishShield-Engine** is an AI-powered email security platform. The security engineer is responsible for the deterministic forensic scanning layer that runs alongside ML models. This layer consists of 10 independent security scanners (homograph detection, brand spoofing, URL obfuscation, header forensics, etc.) that feed into a weighted risk scoring engine (0–100 scale).

## Relevant Directories

| Directory | Purpose |
|-----------|---------|
| `src/security/` | All forensic scanner modules (10 scanners) |
| `src/security/risk_scoring.py` | Central risk aggregation and scoring (0–100) |
| `src/security/url_features.py` | URL analysis (IP detection, suspicious TLDs, Cyrillic) |
| `src/security/homograph_detector.py` | IDN homograph attack detection |
| `src/security/brand_spoof_detector.py` | Fuzzy brand impersonation detection (15+ brands) |
| `src/security/header_analyzer.py` | SPF/DKIM/DMARC header forensics |
| `src/security/obfuscation_detector.py` | Zero-width character detection |
| `src/security/threat_intel.py` | Threat intelligence database operations |
| `src/security/alerts.py` | Security alert triggers |
| `config/config.yaml` | Security weights, thresholds, compliance rules |
| `config/alert_rules.yml` | Prometheus alerting rules |
| `data/threat_intel.db` | Local threat intelligence SQLite database |
| `data/security_alerts.log` | Security incident log output |

## Key Configuration

Security weights and thresholds are controlled via `config/config.yaml`:

```yaml
security:
  weights:
    homograph: 40
    brand_spoof: 45
    domain_blacklist: 60
    header_spoof: 40
    cyrillic_url: 50
    # ... more weights
  thresholds:
    high_risk: 75
    suspicious: 30
```

## Common Workflows

### Run full security analysis on email text

```bash
python -c "
from src.security.risk_scoring import calculate_security_risk
result = calculate_security_risk(
    'Urgent: Your PayPal account is locked. Click http://192.168.1.1/verify',
    'From: support@paypa1.com\nReturn-Path: evil@hacker.io'
)
print(f'Risk Score: {result[\"risk_score\"]}')
print(f'Risk Level: {result[\"risk_level\"]}')
print(f'Flags: {result[\"security_flags\"]}')
print(f'Reasons: {result[\"threat_reasons\"]}')
"
```

### Block a malicious domain

```bash
python cli/manage.py block evil-phishing-site.com --reason "Active credential harvesting campaign"
```

### Run all unit tests for security modules

```bash
python -m pytest tests/test_security_features.py -v
```

### Test specific scanner in isolation

```bash
python -c "
from src.security.homograph_detector import detect_homograph
result = detect_homograph('Visit https://xn--pple-43d.com')
print(result)
"
```

### Add a new security weight or flag

1. Add detection logic in a new module under `src/security/`
2. Register the module in `src/security/risk_scoring.py` `calculate_security_risk()`
3. Add the weight to `config/config.yaml` under `security.weights`
4. Add the flag name to `security_flags` dict in the return value

### View security metrics and threat DB stats

```bash
python cli/manage.py metrics
```

### Export a forensic report

The `POST /export-report` endpoint generates a complete forensic breakdown:

```json
{
  "timestamp": "2026-06-23T...",
  "extracted_urls": ["http://192.168.1.1/verify"],
  "forensic_analysis": { ... }
}
```

## Alerting & Monitoring

- Security alerts are logged to `data/security_alerts.log`
- Prometheus metrics exposed at `GET /metrics`
- Alert rules at `config/alert_rules.yml` for Grafana dashboarding
- Background security alerts dispatched via ARQ Redis worker when `risk_score >= 75`
