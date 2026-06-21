"""
Automated Retraining Scheduler (Phase 76).
Monitors feedback volume and triggers retraining when thresholds are exceeded.
"""

import time
from src.utils.logger import logger
from src.utils.config_loader import settings
from src.core.database import SessionLocal, Feedback

RETRAIN_THRESHOLD = settings.get("models.retrain_threshold", 100)
CHECK_INTERVAL = 3600  # Hourly

def check_and_retrain():
    """Trigger model retraining if enough new feedback exists."""
    session = SessionLocal()
    try:
        count = session.query(Feedback).count()

        if count >= RETRAIN_THRESHOLD:
            logger.info("Retraining Triggered: %d new samples reached threshold.", count)
            # In a real system, this would call a training script or worker
            # os.system("python src/models/train.py --incremental")
            print(f"--- [AUTO-RETRAIN] Triggered with {count} samples ---")
        else:
            print(f"Retrain check: {count}/{RETRAIN_THRESHOLD} samples. Waiting for more data.")

    except Exception as e:
        logger.error("Retraining Scheduler Error: %s", e)
    finally:
        session.close()

if __name__ == "__main__":
    while True:
        check_and_retrain()
        time.sleep(CHECK_INTERVAL)
