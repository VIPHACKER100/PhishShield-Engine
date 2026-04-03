# 🚨 PhishShield-Engine Security Flags

PhishShield-Engine uses a deterministic, rule-based forensic scanning engine that runs alongside the machine learning models. Every time an email is analyzed, the system returns a `security_flags` object containing booleans for multiple distinct threats, and calculates a `security_risk_score` from `0` to `100`.

This document explains each of the 9 primary security flags the engine looks for.

---

## 1. Homograph Detection (`homograph`)

**What it is:** A homograph attack (or IDN spoofing) occurs when an attacker registers a domain name that looks identical or very similar to a legitimate domain name by using characters from different alphabets or scripts.

- **Example:** Spoofing `apple.com` using the Cyrillic `а` (U+0430) instead of the Latin `a` (U+0061).
- **How we detect it:** The engine parses all extracted URLs, normalizes them, and detects punycode (`xn--`) or checks the character script sets via the `unicodedata` library.

## 2. Mixed Script Vectors (`mixed_script`)

**What it is:** Often paired with homograph attacks, mixed script vectors involve combining multiple foreign language scripts within the same contiguous word or domain.

- **Example:** `Ρaypal.com` (combining a Greek Rho `Ρ` with Latin text).
- **How we detect it:** The `script_detector.py` module calculates the script entropy and distribution. If a single word transitions between Latin, Cyrillic, or Greek sub-blocks unexpectedly, it is flagged.

## 3. Brand Spoofing (`brand_spoof`)

**What it is:** Attackers frequently impersonate high-value targets (banks, e-commerce, cloud providers) to steal credentials.

- **Example:** Supposed emails from `Amazon Support` linking to `amazn-security-update.com`.
- **How we detect it:** The `brand_spoof_detector.py` engine utilizes a Levenshtein distance algorithm to fuzzy-match extracted domains against our internal global `target_brands` list in `config.yaml`.

## 4. IP-Based URLs (`ip_url`)

**What it is:** Legitimate bulk senders use actual hostnames to direct users to their sites. Attackers, preferring disposable infrastructure, will often link raw IPv4 or IPv6 addresses directly to bypass DNS filtering.

- **Example:** `http://192.168.1.55/login.php`
- **How we detect it:** Pattern matching in `url_features.py` (via `url_extractor.py`) searches the host value of every URL in the email body for direct IPv4 and IPv6 address formations.

## 5. Header Forgery (`header_spoof`)

**What it is:** Email sender addresses are trivial to forge. The `From:` field shown to the user might not match the actual `Return-Path:` or underlying sender infrastructure.

- **Example:** An email signed by `CEO@mycompany.com` that actually originated from `hacker@evilserver.ru`.
- **How we detect it:** If raw email headers are provided to the API, `header_analyzer.py` verifies SPF (Sender Policy Framework), DKIM, and DMARC alignment. It explicitly diffs the `Return-Path` against the display `From` banner.

## 6. Zero-Width Obfuscation (`obfuscation`)

**What it is:** Spam filters search for specific keywords like "Bitcoin", "Viagra", or "Invoice". Attackers bypass naive regex filters by injecting invisible zero-width characters inside those words.

- **Example:** `B[ZERO_WIDTH]itcoin` — renders exactly as "Bitcoin" to the human eye, but breaks legacy ML sequence parsing.
- **How we detect it:** `obfuscation_detector.py` searches the unicode character sequence for ZWNJ (`\u200C`), ZWJ (`\u200D`), and other invisible artifacts.

## 7. Suspicious TLD / Domain Risk (`domain_risk`)

**What it is:** A domain ending in a suspicious or highly abused TLD (Top-Level Domain) is inherently riskier than standard TLDs.

- **Example:** Linking to `.xyz`, `.biz`, or `.tk`.
- **How we detect it:** Domains are matched against the local `threatDB` (SQLite), and their TLDs are checked against a configured list of high-risk extensions.

## 8. Suspicious URL Formats (`suspicious_url`)

**What it is:** Attackers often chain redirects, heavily encode URLs, or pad URLs with hyphens and subdomains to prevent standard analysis tools from finding the root server.

- **Example:** `http://secure-login-update-account-info-paypal.com.evil.co`
- **How we detect it:** Evaluates the sub-domain depth, URL entropy, the presence of `@` symbols used to mask auth-creds, and URL length (`url_features.py`).

## 9. Behavioral Threat Analysis (`behavioral_threat`)

**What it is:** Urgent requests or financial extortion language within the email body. Phishing relies on psychological manipulation.

- **Example:** *"Your account will be suspended in 24 hours. Act now."*
- **How we detect it:** NLP analysis of the cleaned text looking for extreme urgency indicators, arbitrary deadlines, and financial reward/threat bait (`text_behavior.py`).

---

## Conclusion

The aggregate output of these 9 flags is weighted. For example, `brand_spoof` combined with `ip_url` instantly forces a `High Risk (Score: 85+)` rating, ensuring even if the ML model is unsure due to adversarial text tricks, the forensic scanning accurately catches the attack!
