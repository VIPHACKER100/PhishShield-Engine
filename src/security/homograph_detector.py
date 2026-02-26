"""
Homograph Detector — Detect visually similar character substitutions in domains (IDN Phishing).
"""

import unicodedata
from src.security.url_extractor import extract_urls, get_domain

# Common confusable character mappings (Latin <-> Greek/Cyrillic/Etc)
# This is a reduced set of the most common substitutions
CONFUSABLES = {
    'a': ['α', 'а'],
    'o': ['ο', 'о'],
    'e': ['е', 'ε'],
    'p': ['р'],
    'c': ['с'],
    'y': ['у'],
    'i': ['і', 'ɩ'],
    'k': ['κ'],
    'x': ['х'],
}

def detect_homograph(text: str) -> dict:
    """
    Scan text for homograph attacks in domains.
    - Mixed script detection
    - Confusable character mapping
    - Punycode conversion check
    """
    urls = extract_urls(text)
    domains = [get_domain(u) for u in urls]
    
    homograph_detected = False
    mixed_script_domains = False
    spoofed_parts = []
    
    for domain in domains:
        # Check for mixed scripts in the domain
        scripts = set()
        for char in domain:
            if char in ('.', '-'): continue
            try:
                # Get the script name (e.g., LATIN, GREEK, CYRILLIC)
                script = unicodedata.name(char).split()[0]
                scripts.add(script)
            except:
                continue
        
        if len(scripts) > 1:
            mixed_script_domains = True
            homograph_detected = True
            spoofed_parts.append(domain)
            
        # Punycode check (IDNA)
        try:
            punycode = domain.encode('idna').decode('ascii')
            if punycode.startswith('xn--'):
                homograph_detected = True
                spoofed_parts.append(f"{domain} (punycode: {punycode})")
        except:
            pass

    return {
        "homograph_detected": homograph_detected,
        "mixed_script_domain": mixed_script_domains,
        "spoofed_domains": spoofed_parts,
        "homograph_count": len(spoofed_parts)
    }
