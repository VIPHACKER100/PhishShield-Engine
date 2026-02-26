"""
Domain Intelligence — Analyze domain reputation and age-based risk factors.
"""

from src.security.threat_intel import check_domain_reputation
from src.security.url_normalizer import normalize_url

def analyze_domain_intelligence(urls: list[str]) -> dict:
    """
    Perform deep analysis on domains found in URLs.
    """
    results = {
        "max_risk_score": 0,
        "threat_flags": [],
        "known_malicious_count": 0,
        "details": []
    }
    
    unique_domains = set()
    for url in urls:
        norm = normalize_url(url)
        domain = norm.get("normalized_host")
        if domain:
            unique_domains.add(domain)
            
    for domain in unique_domains:
        rep = check_domain_reputation(domain)
        
        domain_threats = []
        domain_score = 0
        
        if rep["known_threat"]:
            domain_threats.append(f"Known threat: {rep['reason']}")
            domain_score += 80
            results["known_malicious_count"] += 1
            
        # Basic heuristic: Domain length
        if len(domain) > 30:
            domain_threats.append("Excessively long domain name")
            domain_score += 10
            
        # Check for numeric domains (very suspicious)
        # e.g. 192.168.1.1 (already handled in url_features, but check for 123-app.top)
        if any(c.isdigit() for c in domain.split('.')[0]):
            domain_score += 5
            
        if domain_score > 0:
            results["details"].append({
                "domain": domain,
                "score": domain_score,
                "threats": domain_threats
            })
            results["max_risk_score"] = max(results["max_risk_score"], domain_score)
            results["threat_flags"].extend(domain_threats)

    # Clean duplicates
    results["threat_flags"] = list(set(results["threat_flags"]))
    return results
