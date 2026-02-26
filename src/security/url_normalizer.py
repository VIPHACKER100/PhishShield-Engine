"""
URL Normalizer — Clean and standardize URLs to prevent evasion.
"""

import re
from urllib.parse import urlparse, unquote

def normalize_url(url: str) -> dict:
    """
    Standardize a URL for reliable threat analysis.
    - Decodes encodings
    - Removes defaults (ports, trailing slashes)
    - Extracts components
    """
    try:
        # Decode URL-encoded characters (e.g., %20 -> space)
        url = unquote(url).strip()
        
        # Add scheme if missing for parsing
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        parsed = urlparse(url)
        
        # Basic normalization
        host = parsed.netloc.lower()
        if host.startswith('www.'):
            host = host[4:]
            
        # Remove default ports
        if ':' in host:
            host, port = host.split(':', 1)
            if (parsed.scheme == 'http' and port == '80') or (parsed.scheme == 'https' and port == '443'):
                pass # keep host as is
            else:
                host = f"{host}:{port}"
                
        path = parsed.path.rstrip('/')
        
        return {
            "original": url,
            "normalized_host": host,
            "path": path,
            "scheme": parsed.scheme,
            "query": parsed.query,
            "full_normalized": f"{parsed.scheme}://{host}{path}"
        }
    except Exception:
        return {"original": url, "normalized_host": url, "error": "Normalization failed"}

def get_normalized_domains(urls: list[str]) -> list[str]:
    """Helper to get list of clean domains."""
    return [normalize_url(u)["normalized_host"] for u in urls]
