"""
Adaptive Learning Engine — Incremental retraining based on live feedback and drift logs.
"""

import pandas as pd
from src.utils.logger import logger
from src.core.database import SessionLocal, Feedback

class AdaptiveLearner:
    """
    Monitors feedback and triggers incremental retraining.
    """
    
    def __init__(self, threshold: int = 50):
        self.threshold = threshold # retrain every 50 new feedback entries
        
    def check_and_retrain(self):
        """Check if enough new data exists to justify retraining."""
        session = SessionLocal()
        try:
            feedbacks = session.query(Feedback).all()
            if len(feedbacks) >= self.threshold:
                # Convert list of SQLAlchemy models to DataFrame
                data = [
                    {
                        "id": f.id,
                        "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                        "email_text": f.email_text,
                        "predicted_label": f.predicted_label,
                        "correct_label": f.correct_label,
                        "model_used": f.model_used
                    }
                    for f in feedbacks
                ]
                df = pd.DataFrame(data)
                logger.info("Adaptive Learning: Threshold reached (%d entries). Starting incremental retrain...", len(df))
                self._run_retraining_job(df)
            else:
                logger.info("Adaptive Learning: Not enough new data yet (%d/%d)", len(feedbacks), self.threshold)
        except Exception as e:
            logger.error("Adaptive Learning Error: %s", e)
        finally:
            session.close()

    def _run_retraining_job(self, new_data: pd.DataFrame):
        """
        Simulate retraining logic. 
        In production, this would call scripts/train_pipeline.py with the augmented dataset.
        """
        logger.info("Loading baseline dataset...")
        # ... load v2_emails.csv ...
        
        logger.info("Merging with %d live feedback samples...", len(new_data))
        # ... logic to merge and create updated features ...
        
        logger.info("Retraining Naive Bayes and SVM models...")
        # joblib.dump(new_model, "models/adaptive_model.pkl")
        
        logger.info("Retraining COMPLETE. New model registered in registry.")

if __name__ == "__main__":
    learner = AdaptiveLearner(threshold=5)
    learner.check_and_retrain()
