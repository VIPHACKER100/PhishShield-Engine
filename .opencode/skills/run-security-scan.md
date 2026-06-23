# Skill: Run Security Analysis

## Description

Executes the PhishShield-Engine forensic security scanning pipeline against email text. Runs all 10 independent security scanners (homograph, brand spoofing, URL obfuscation, header forensics, etc.) and returns a weighted risk score (0–100) with detailed threat reasons and security flags.

## Prerequisites

- Python environment with dependencies installed
- Virtual environment activated
- Working directory at project root

## Workflow Steps

### 1. Run full security analysis via Python

```bash
python -c "
from src.security.risk_scoring import calculate_security_risk
result = calculate_security_risk(
    'Urgent: Your PayPal account has been compromised. '
    'Click http://192.168.1.1/verify to restore access.',
    'From: support@paypa1.com\nReturn-Path: evil@hacker.io'
)
print('Risk Score:', result['risk_score'])
print('Risk Level:', result['risk_level'])
print('Threat Reasons:', result['threat_reasons'])
print('Security Flags:', result['security_flags'])
"
```

### 2. Run via API endpoint

```bash
curl -X POST http://localhost:8000/analyze-security \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Verify your Amazon account at http://192.168.1.1",
    "headers": "From: amazon-security@evil.com"
  }' | python -m json.tool
```

### 3. Run individual scanner tests

```bash
# Homograph detection
python -c "
from src.security.homograph_detector import detect_homograph
print(detect_homograph('Visit https://xn--pple-43d.com'))
"

# Brand spoof detection
python -c "
from src.security.brand_spoof_detector import detect_brand_impersonation
print(detect_brand_impersonation('Your PayPal account is locked', ['http://paypa1.com']))
"

# Obfuscation detection
python -c "
from src.security.obfuscation_detector import detect_obfuscation
print(detect_obfuscation('Fr\u200Bee money'))
"

# URL feature extraction
python -c "
from src.security.url_features import get_url_security_features
print(get_url_security_features('Check http://192.168.1.1 and http://bit.ly/abc'))
"

# Header analysis
python -c "
from src.security.header_analyzer import analyze_headers, parse_headers
parsed = parse_headers('From: ceo@company.com\nReturn-Path: hacker@evil.com')
print(analyze_headers(parsed))
"
```

### 4. Run security test suite

```bash
python -m pytest tests/test_security_features.py -v
```

### 5. Generate forensic export report

```bash
curl -X POST http://localhost:8000/export-report \
  -H "Content-Type: application/json" \
  -d '{"text": "Urgent payment at http://bit.ly/abc"}' | python -m json.tool
```

## All 10 Security Flags

| Flag | Description | Default Weight |
|------|-------------|----------------|
| `homograph` | IDN homograph attack (lookalike domains) | 40 |
| `mixed_script` | Mixed Unicode scripts in text | 25 |
| `brand_spoof` | Brand impersonation (PayPal, Amazon, etc.) | 45 |
| `ip_url` | Direct IP address in URL | 45 |
| `header_spoof` | SPF/DKIM/DMARC header forgery | 40 |
| `obfuscation` | Zero-width characters in text | 35 |
| `domain_risk` | Known malicious domain match | 60 |
| `suspicious_url` | Suspicious URL patterns | 20 |
| `behavioral_threat` | Urgency/reward bait language | 15 |
| `cyrillic_url` | Cyrillic characters in URL | 50 |

## Risk Levels

| Score Range | Level |
|-------------|-------|
| 0–29 | LOW |
| 30–74 | SUSPICIOUS |
| 75–100 | HIGH RISK |

## Configuration

All security weights and thresholds are in `config/config.yaml` under `security:`:

```yaml
security:
  weights:
    homograph: 40
    brand_spoof: 45
    domain_blacklist: 60
    cyrillic_url: 50
    # ...
  thresholds:
    high_risk: 75
    suspicious: 30
```

## Verification

```bash
# Validate scanner is working
python -c "
from src.security.risk_scoring import calculate_security_risk
result = calculate_security_risk('http://192.168.1.1')
assert result['risk_score'] > 0
assert result['security_flags']['ip_url'] == True
print('Security scanning operational')
"
```
