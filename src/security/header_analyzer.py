"""
Header Analyzer — Detect email spoofing and header anomalies.
"""

import re
from src.utils.logger import logger

def parse_headers(raw_headers: str) -> dict:
    """
    Very basic parser for email header strings.
    In a real app, use email.parser.
    """
    headers = {}
    lines = raw_headers.splitlines()
    for line in lines:
        if ':' in line:
            key, val = line.split(':', 1)
            headers[key.strip().lower()] = val.strip()
    return headers

def analyze_headers(headers: dict) -> dict:
    """
    Check for common spoofing signals:
    - From vs Return-Path mismatch
    - Suspicious Reply-To
    - MISSING SPF/DKIM/DMARC signs
    """
    results = {
        "is_spoofed": False,
        "mismatched_domains": False,
        "suspicious_relay": False,
        "missing_security": False,
        "threats": []
    }

    from_field = headers.get('from', '')
    return_path = headers.get('return-path', '')
    reply_to = headers.get('reply-to', '')
    
    # 1. From vs Return-Path check
    if from_field and return_path:
        from_domain = re.search(r'@([\w.-]+)', from_field)
        rp_domain = re.search(r'@([\w.-]+)', return_path)
        
        if from_domain and rp_domain and from_domain.group(1) != rp_domain.group(1):
            results["is_spoofed"] = True
            results["mismatched_domains"] = True
            results["threats"].append("From domain mismatch with Return-Path")

    # 2. Reply-To sanity
    if reply_to and from_field:
        if reply_to.lower() != from_field.lower():
            results["threats"].append("Reply-To differs from From address")

    # 3. Check for auth results (simulated)
    auth_res = headers.get('authentication-results', '')
    if auth_res:
        if 'spf=fail' in auth_res.lower() or 'spf=softfail' in auth_res.lower():
            results["is_spoofed"] = True
            results["threats"].append("SPF authentication failed")
        if 'dkim=fail' in auth_res.lower():
            results["is_spoofed"] = True
            results["threats"].append("DKIM authentication failed")

    return results
