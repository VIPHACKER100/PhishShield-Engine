"""
Risk Scoring & Rules Engine — Heuristic-based security analysis and threat levels.
"""

from src.security.url_features import get_url_security_features
from src.security.homograph_detector import detect_homograph
from src.security.script_detector import detect_script_types
from src.security.brand_spoof_detector import detect_brand_impersonation
from src.security.text_behavior import analyze_text_behavior
from src.security.url_extractor import extract_urls

from src.security.domain_intelligence import analyze_domain_intelligence
from src.security.header_analyzer import analyze_headers, parse_headers
from src.security.obfuscation_detector import detect_obfuscation
from src.utils.logger import logger

from src.utils.config_loader import settings

def calculate_security_risk(text: str, raw_headers: str = "") -> dict:
    """
    Apply multi-layer rule detection and calculate risk score (0-100).
    Uses weights and thresholds from centralized config.
    """
    urls = extract_urls(text)
    url_feats = get_url_security_features(text)
    homograph_feats = detect_homograph(text)
    script_feats = detect_script_types(text)
    brand_feats = detect_brand_impersonation(text, urls)
    behavior_feats = analyze_text_behavior(text)
    domain_feats = analyze_domain_intelligence(urls)
    obfuscation_feats = detect_obfuscation(text)
    
    # Load weights from config
    w = settings.get("security.weights", {})
    
    # Header analysis
    header_feats = {"is_spoofed": False, "threats": []}
    if raw_headers:
        parsed = parse_headers(raw_headers)
        header_feats = analyze_headers(parsed)
    
    score = 0
    reasons = []
    
    # 1. Critical Threats (Known Data)
    d_threats = domain_feats.get("threat_flags", [])
    if d_threats and isinstance(d_threats, list):
        score += w.get("domain_blacklist", 60)
        reasons.extend(d_threats)
        
    if header_feats.get("is_spoofed") and isinstance(header_feats.get("threats"), list):
        score += w.get("header_spoof", 40)
        reasons.extend(header_feats["threats"])

    # 2. Heuristic Threats
    if obfuscation_feats["is_obfuscated"]:
        score += 35
        reasons.extend(obfuscation_feats["threats"])

    if homograph_feats["homograph_detected"]:
        score += w.get("homograph", 40)
        reasons.append("Homograph (IDN) attack detected")
    
    if script_feats["mixed_script"]:
        score += w.get("mixed_script", 25)
        reasons.append("Mixed Unicode scripts detected")

    if brand_feats["brand_impersonation_detected"]:
        score += w.get("brand_spoof", 45)
        reasons.append(f"Brand Impersonation detected: {', '.join(brand_feats['impersonated_brands'])}")
        
    if behavior_feats["behavior_score"] > w.get("behavioral_threshold", 40):
        score += w.get("behavioral_low", 15)
        reasons.append("Suspicious writing behavior (Urgency/Reward Bait)")
        
    if url_feats["has_ip_url"]:
        score += w.get("ip_url", 45)
        reasons.append("Url contains direct IP address")
        
    if url_feats["suspicious_tld_count"] > 0:
        score += w.get("suspicious_tld", 20) * url_feats["suspicious_tld_count"]
        reasons.append(f"Suspicious TLD(s) detected: {url_feats['suspicious_tld_count']}")
        
    if url_feats["has_shortener"]:
        score += w.get("url_shortener", 15)
        reasons.append("URL shortener used")
        
    if url_feats["url_count"] > 3:
        score += w.get("multiple_urls", 10)
        reasons.append("Multiple URLs detected (> 3)")

    # Cap score at 100
    risk_score = min(score, 100)
    
    # Derive risk level from config thresholds
    thresholds = settings.get("security.thresholds", {"high_risk": 75, "suspicious": 30})
    if risk_score > thresholds["high_risk"]:
        risk_level = "HIGH RISK"
    elif risk_score > thresholds["suspicious"]:
        risk_level = "SUSPICIOUS"
    else:
        risk_level = "LOW"
        
    logger.info("Security Risk Analysis: score=%d, reasons=%s", risk_score, reasons)
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "threat_reasons": list(set(reasons)),
        "security_flags": {
            "homograph": homograph_feats["homograph_detected"],
            "mixed_script": script_feats["mixed_script"],
            "suspicious_url": url_feats["is_url_suspicious"],
            "brand_spoof": brand_feats["brand_impersonation_detected"],
            "ip_url": url_feats["has_ip_url"],
            "behavioral_threat": behavior_feats["behavior_score"] > 50,
            "domain_risk": domain_feats["known_malicious_count"] > 0,
            "header_spoof": header_feats["is_spoofed"],
            "obfuscation": obfuscation_feats["is_obfuscated"]
        },
        "details": {
            "urls": url_feats,
            "scripts": script_feats,
            "homograph": homograph_feats,
            "brand": brand_feats,
            "behavior": behavior_feats,
            "domain_intel": domain_feats,
            "headers": header_feats,
            "obfuscation": obfuscation_feats
        }
    }


def run_security_rules(text: str, raw_headers: str = "") -> dict:
    """Fastheuristic filter for rule-based overrides."""
    analysis = calculate_security_risk(text, raw_headers)
    
    # Decision: Auto-flag as spam if risk is very high
    is_rule_spam = analysis["risk_score"] >= 75
    
    return {
        "is_rule_spam": is_rule_spam,
        "risk_analysis": analysis
    }
