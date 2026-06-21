"""
Security Rule Engine (Phase 45)
Overrides ML logic when specific fatal heuristics are triggered.
"""

def run_security_rules(security_flags: dict, risk_score: int) -> dict:
    """
    Decides if a deterministic rule should immediately trigger a Spam classification,
    ignoring what the Scikit-learn predictive engine outputted.
    """
    reasons = []
    override_spam = False

    if security_flags.get("ip_url"):
        reasons.append("Url contains direct IP address")
        override_spam = True
        
    if security_flags.get("homograph"):
        reasons.append("Homograph visual spoiler detected")
        override_spam = True
        
    if security_flags.get("cyrillic_url"):
        reasons.append("Suspicious Cyrillic characters in URL detected")
        override_spam = True

        
    if risk_score > 75:
        reasons.append("Aggregate forensic risk critically high")
        override_spam = True
        
    if security_flags.get("mixed_script"):
        reasons.append("Highly suspicious Unicode mixed-scripts detected")
        override_spam = True

    return {
        "rule_spam_flag": override_spam,
        "reason": reasons
    }
