"""
URL Extractor — Detect URLs, domains, and suspicious link patterns in email text.
"""

import re
from typing import List

# Improved URL detection regex
URL_PATTERN = re.compile(
    r'(?:http|https)://[^\s/$.?#].[^\s]*'  # http/https
    r'|www\.[^\s/$.?#].[^\s]*'              # www.
    r'|[a-zA-Z0-9.-]+\.(?:com|net|org|edu|gov|io|biz|info|xyz|top|click|gq|tk|ml|ga|cf)\b' # domain-like
)

def extract_urls(text: str) -> List[str]:
    """Extract all URLs and domain-like strings from text."""
    return URL_PATTERN.findall(text)

def get_domain(url: str) -> str:
    """Extract domain part from a URL string."""
    domain = url.lower()
    if domain.startswith(('http://', 'https://')):
        domain = domain.split('//')[1]
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain.split('/')[0].split('?')[0]
