"""
Advanced Deep Learning Module
Uses HuggingFace Transformers for semantic phishing and spam detection.
"""
import logging
from transformers import pipeline

class DeepLearningModel:
    def __init__(self, model_name: str = "ealvaradob/bert-finetuned-phishing"):
        self.model_name = model_name
        self.classifier = None
        self.is_loaded = False
        
    def load(self):
        """Load the transformer model into memory."""
        logging.info("Loading Deep Learning transformer: %s", self.model_name)
        try:
            self.classifier = pipeline("text-classification", model=self.model_name, truncation=True, max_length=512)
            self.is_loaded = True
        except Exception as e:
            logging.error(f"Failed to load transformer model: {e}")
            raise

    def predict(self, text: str) -> dict:
        """Process text sequences using transformer."""
        if not self.is_loaded:
            self.load()
        
        result = self.classifier(text)[0]
        label = result['label'].lower()
        
        # Typically LABEL_1 is Phishing/Spam in binary classifications
        prediction = "spam" if "phishing" in label or "spam" in label or label == "label_1" else "ham"
        
        return {
            "prediction": prediction, 
            "confidence": round(result['score'], 4),
            "model_used": self.model_name
        }
