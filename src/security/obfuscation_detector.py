"""
Obfuscation Detector — Detects invisible characters and evasion tricks (Phase 85).
Zero-width characters, homoglyphs, and other bypass techniques.
"""

import re
from src.utils.logger import logger

# Zero-width spaces, joiners, and other invisible markers
INVISIBLE_CHARS_PATTERN = r'[\u200B-\u200D\uFEFF\u00AD\u2060]'

def detect_obfuscation(text: str) -> dict:
    """Detect hidden/invisible characters used to bypass spam filters."""
    matches = re.findall(INVISIBLE_CHARS_PATTERN, text)
    count = len(matches)
    
    # Check for excessive character repetition (another evasion trick)
    repetition = False
    if re.search(r'(.)\1{10,}', text):
        repetition = True
        
    # Check for excessive punctuation / symbol ratio
    symbols = len(re.findall(r'[^\w\s]', text))
    symbol_ratio = symbols / len(text) if len(text) > 0 else 0
    
    is_obfuscated = count > 0 or repetition or symbol_ratio > 0.4
    
    threats = []
    if count > 0:
        threats.append(f"Detected {count} zero-width / invisible characters")
    if repetition:
        threats.append("Excessive character repetition detected")
    if symbol_ratio > 0.4:
        threats.append(f"Suspicious symbol ratio: {symbol_ratio:.1%}")

    return {
        "is_obfuscated": is_obfuscated,
        "invisible_count": count,
        "symbol_ratio": symbol_ratio,
        "threats": threats
    }

if __name__ == "__main__":
    test_text = "Free G\u200Bift Ca\u200Brd"
    print(detect_obfuscation(test_text))
