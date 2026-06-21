"""
Compliance & Data Governance — Automated retention and audit logging (Phase 72).
"""

import os
from datetime import datetime, timedelta, timezone
from src.utils.logger import logger
from src.utils.config_loader import settings
from src.core.database import SessionLocal, Feedback

COMPLIANCE_LOG = settings.get("compliance.log_path", "logs/compliance.log")
RETENTION_DAYS = settings.get("compliance.retention_days", 30)

def log_compliance_event(event_type: str, details: str):
    """Secure audit log for regulatory compliance (GDPR/ISO)."""
    os.makedirs(os.path.dirname(COMPLIANCE_LOG), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(COMPLIANCE_LOG, "a") as f:
        f.write(f"{timestamp} | {event_type} | {details}\n")

def enforce_data_retention():
    """Delete sensitive email entries older than the retention threshold."""
    session = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
        
        # Count items to be deleted for audit
        to_delete = session.query(Feedback).filter(Feedback.timestamp < cutoff)
        count = to_delete.count()
        
        if count > 0:
            to_delete.delete(synchronize_session=False)
            session.commit()
            log_compliance_event("DATA_RETENTION", f"Deleted {count} expired records (older than {RETENTION_DAYS} days)")
            logger.info("Compliance: Cleaned up %d expired feedback records.", count)
            
    except Exception as e:
        session.rollback()
        logger.error("Data Retention Error: %s", e)
    finally:
        session.close()

if __name__ == "__main__":
    enforce_data_retention()
