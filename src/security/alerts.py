"""
Alerting System — Trigger notifications for high-risk security events.
"""

from src.utils.logger import logger
from datetime import datetime

def trigger_security_alert(event_type: str, details: dict):
    """
    Simulate an enterprise alerting system (Email, Slack, Webhook).
    """
    risk_score = details.get("security_risk_score", 0)
    
    if risk_score >= 90:
        alert_level = "CRITICAL"
    elif risk_score >= 75:
        alert_level = "WARNING"
    else:
        return # No alert for low risk

    alert_payload = {
        "timestamp": datetime.now().isoformat(),
        "level": alert_level,
        "type": event_type,
        "reasons": details.get("threat_reasons", []),
        "email_preview": details.get("email_text", "")[:100] + "..."
    }
    
    # In a real system, you'd send this to PagerDuty or an ELK stack.
    logger.warning("!!! SECURITY ALERT [%s] !!! %s", alert_level, alert_payload)
    
    # Store in a local alert log for forensic dashboard (Phase 63)
    _log_alert_to_file(alert_payload)

def _log_alert_to_file(payload: dict):
    alert_file = "data/security_alerts.log"
    with open(alert_file, "a") as f:
        f.write(f"{payload['timestamp']} | {payload['level']} | {payload['reasons']}\n")
