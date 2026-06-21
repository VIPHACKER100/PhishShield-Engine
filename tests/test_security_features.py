import pytest

def test_url_extraction():
    from src.security.url_extractor import extract_urls
    text = "Check this out: http://evil.com and https://192.168.1.1/login"
    urls = extract_urls(text)
    assert len(urls) == 2
    assert set(urls) == {"http://evil.com", "https://192.168.1.1/login"}

def test_homograph_detection():
    from src.security.homograph_detector import detect_homograph
    # "apple" using Cyrillic 'а'
    text = "Visit https://аpple.com"
    result = detect_homograph(text)
    assert result.get("homograph_detected", False) is True

def test_script_detection():
    from src.security.script_detector import detect_script_types
    text = "Paypаl login" # mixed Latin and Cyrillic
    result = detect_script_types(text)
    assert result.get("mixed_script", False) is True

def test_risk_scoring():
    from src.security.risk_scoring import calculate_security_risk
    text = "Urgent: Verify your account at http://192.168.1.55"
    result = calculate_security_risk(text)
    assert result.get("risk_score", 0) > 30
    flags = result.get("security_flags", {})
    assert flags.get("ip_url", False) is True

def test_cyrillic_url_detection():
    from src.security.risk_scoring import calculate_security_risk
    text = "Visit https://вася.com"
    result = calculate_security_risk(text)
    assert result.get("risk_score", 0) >= 50
    flags = result.get("security_flags", {})
    assert flags.get("cyrillic_url", False) is True
