"""
Compliance & Data Governance — Automated retention and audit logging (Phase 72).
"""

import os
import time
import sqlite3
from datetime import datetime, timedelta
from src.utils.logger import logger
from src.utils.config_loader import settings

COMPLIANCE_LOG = settings.get("compliance.log_path", "logs/compliance.log")
RETENTION_DAYS = settings.get("compliance.retention_days", 30)

def log_compliance_event(event_type: str, details: str):
    """Secure audit log for regulatory compliance (GDPR/ISO)."""
    os.makedirs(os.path.dirname(COMPLIANCE_LOG), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(COMPLIANCE_LOG, "a") as f:
        f.write(f"{timestamp} | {event_type} | {details}\n")

def enforce_data_retention():
    """Delete sensitive email entries older than the retention threshold."""
    feedback_db = "data/feedback.db"
    if not os.path.exists(feedback_db):
        return

    try:
        cutoff = (datetime.now() - timedelta(days=RETENTION_DAYS)).isoformat()
        conn = sqlite3.connect(feedback_db)
        c = conn.cursor()
        
        # Count items to be deleted for audit
        c.execute("SELECT COUNT(*) FROM feedback WHERE timestamp < ?", (cutoff,))
        count = c.fetchone()[0]
        
        if count > 0:
            c.execute("DELETE FROM feedback WHERE timestamp < ?", (cutoff,))
            conn.commit()
            log_compliance_event("DATA_RETENTION", f"Deleted {count} expired records (older than {RETENTION_DAYS} days)")
            logger.info("Compliance: Cleaned up %d expired feedback records.", count)
            
        conn.close()
    except Exception as e:
        logger.error("Data Retention Error: %s", e)

if __name__ == "__main__":
    enforce_data_retention()
