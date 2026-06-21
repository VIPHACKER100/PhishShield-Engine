"""
URL Features — Extract structural and reputation features from URLs.
"""

import re
from src.security.url_extractor import extract_urls, get_domain

SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".gq", ".tk", ".ml", ".ga", ".cf", ".bid", ".men"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly"}

# Regex for IPv4 in URLs
IP_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')

# Regex for Cyrillic characters (basic range U+0400 to U+04FF)
CYRILLIC_PATTERN = re.compile(r'[\u0400-\u04FF]')

def get_url_security_features(text: str) -> dict:
    """Analyze text for URL-based security features."""
    urls = extract_urls(text)
    domains = [get_domain(u) for u in urls]
    
    features = {
        "url_count": len(urls),
        "has_ip_url": any(IP_PATTERN.search(u) for u in urls),
        "has_shortener": any(any(s in d for s in SHORTENERS) for d in domains),
        "suspicious_tld_count": sum(1 for d in domains if any(d.endswith(t) for t in SUSPICIOUS_TLDS)),
        "max_subdomains": max([d.count('.') for d in domains]) if domains else 0,
        "max_hyphens_in_domain": max([d.count('-') for d in domains]) if domains else 0,
        "long_domain_detected": any(len(d) > 25 for d in domains),
        "has_cyrillic": any(CYRILLIC_PATTERN.search(u) for u in urls)
    }
    
    # Suspicious flag for rules engine
    features["is_url_suspicious"] = (
        features["has_ip_url"] or 
        features["has_cyrillic"] or
        features["suspicious_tld_count"] > 0 or 
        features["url_count"] > 3 or
        features["max_subdomains"] > 2
    )
    
    return features
