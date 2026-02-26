"""
Script Detector — Detect suspicious mixing of Latin, Greek, Cyrillic, and other scripts.
"""

import unicodedata
from collections import Counter

def detect_script_types(text: str) -> dict:
    """Analyze the distribution of scripts in the text."""
    if not text:
        return {"latin_ratio": 1.0, "mixed_script": False}

    scripts = []
    for char in text:
        if not char.isalpha():
            continue
        try:
            # e.g., "LATIN SMALL LETTER A" -> "LATIN"
            script = unicodedata.name(char).split()[0]
            scripts.append(script)
        except:
            continue

    if not scripts:
        return {"latin_ratio": 1.0, "mixed_script": False}

    counts = Counter(scripts)
    total = sum(counts.values())
    
    latin_count = counts.get("LATIN", 0)
    greek_count = counts.get("GREEK", 0)
    cyrillic_count = counts.get("CYRILLIC", 0)
    
    # Calculate ratios
    ratios = {
        "latin_ratio": round(latin_count / total, 3),
        "greek_ratio": round(greek_count / total, 3),
        "cyrillic_ratio": round(cyrillic_count / total, 3),
    }

    # Signal mixed scripts if non-Latin scripts are present alongside Latin
    mixed_script = (latin_count > 0 and (greek_count > 0 or cyrillic_count > 0))
    
    return {
        **ratios,
        "mixed_script": mixed_script,
        "script_counts": dict(counts)
    }
