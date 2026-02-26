"""
Brand Spoof Detector — Detect domains mimicking popular brands using string similarity.
"""

from src.security.url_normalizer import get_normalized_domains

# Key brands to protect
PROTECTED_BRANDS = {
    "paypal": ["paypa1", "pypal", "pay-pal", "pay.pal"],
    "google": ["g00gle", "goog1e", "googl-e"],
    "microsoft": ["mircosoft", "micros0ft", "ms-office"],
    "amazon": ["amaz0n", "amzn-service", "amazon-support"],
    "apple": ["app1e", "apple-id", "support-apple"],
    "netflix": ["netf1ix", "net-flix"],
    "binance": ["b1nance", "binance-support"],
    "metamask": ["metamask-support", "mextamask"],
}

def levenshtein_distance(s1: str, s2: str) -> int:
    """Native implementation of Levenshtein distance."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def detect_brand_impersonation(text: str, urls: list[str]) -> dict:
    """
    Check if any URLs in the text are mimicking a protected brand.
    """
    domains = get_normalized_domains(urls)
    
    threats = []
    max_similarity = 0.0
    
    for domain in domains:
        # Check against protected brand names
        main_part = domain.split('.')[0]
        
        for brand in PROTECTED_BRANDS:
            # Skip if it IS the actual brand domain (e.g. apple.com)
            if main_part == brand:
                continue
                
            dist = levenshtein_distance(main_part, brand)
            similarity = 1 - (dist / max(len(main_part), len(brand)))
            
            # Threshold for suspicion
            if similarity > 0.75:
                threats.append({
                    "brand": brand,
                    "spoofed_domain": domain,
                    "similarity": round(similarity, 2)
                })
                max_similarity = max(max_similarity, similarity)
            
            # Also check manual variation list
            for variant in PROTECTED_BRANDS[brand]:
                if variant in main_part:
                    threats.append({
                        "brand": brand,
                        "spoofed_domain": domain,
                        "reason": "Suspicious brand keyword"
                    })
                    max_similarity = max(max_similarity, 0.9)

    return {
        "brand_impersonation_detected": len(threats) > 0,
        "impersonated_brands": list(set([t["brand"] for t in threats])),
        "threat_details": threats,
        "max_brand_similarity": round(max_similarity, 2)
    }
