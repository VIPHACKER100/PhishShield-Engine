"""
Optimized Pipeline — Single serialized prediction pipeline for low-latency inference.
"""

import os
import re
import string
import joblib
import numpy as np
from src.utils.logger import logger

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_NUM_RE = re.compile(r"\d+")

# Pre-load stopwords once
try:
    from nltk.corpus import stopwords as _sw
    _STOPWORDS = frozenset(_sw.words("english"))
except Exception:
    _STOPWORDS = frozenset()

from nltk.stem import PorterStemmer
_STEMMER = PorterStemmer()


class OptimizedPipeline:
    """
    Single object that wraps vectorizer + model for fast, single-call predictions.
    Avoids re-loading from disk on every request.
    """

    def __init__(self, vectorizer_path: str, model_path: str):
        self.vectorizer = joblib.load(vectorizer_path)
        self.model = joblib.load(model_path)
        self._has_proba = hasattr(self.model, "predict_proba")
        logger.info("OptimizedPipeline loaded: vectorizer=%s model=%s", vectorizer_path, model_path)

    def _preprocess(self, text: str) -> str:
        """Optimized preprocessing with compiled regex and cached stopwords."""
        text = text.lower()
        text = text.translate(_PUNCT_TABLE)
        text = _NUM_RE.sub("", text)
        tokens = text.split()
        tokens = [_STEMMER.stem(t) for t in tokens if t not in _STOPWORDS]
        return " ".join(tokens)

    def predict(self, text: str) -> dict:
        cleaned = self._preprocess(text)
        features = self.vectorizer.transform([cleaned])
        prediction = self.model.predict(features)[0]
        confidence = None
        if self._has_proba:
            proba = self.model.predict_proba(features)[0]
            confidence = round(float(max(proba)), 4)
        return {"prediction": prediction, "confidence": confidence}

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """Batch prediction — vectorize all at once for efficiency."""
        cleaned = [self._preprocess(t) for t in texts]
        features = self.vectorizer.transform(cleaned)
        predictions = self.model.predict(features)
        results = []
        if self._has_proba:
            probas = self.model.predict_proba(features)
            for pred, proba in zip(predictions, probas):
                results.append({"prediction": pred, "confidence": round(float(max(proba)), 4)})
        else:
            for pred in predictions:
                results.append({"prediction": pred, "confidence": None})
        return results

    def save(self, path: str):
        """Serialize the entire pipeline as one file."""
        joblib.dump({"vectorizer": self.vectorizer, "model": self.model}, path)
        logger.info("Saved optimized pipeline → %s", path)

    @classmethod
    def load(cls, path: str) -> "OptimizedPipeline":
        """Load a previously saved optimized pipeline."""
        data = joblib.load(path)
        instance = cls.__new__(cls)
        instance.vectorizer = data["vectorizer"]
        instance.model = data["model"]
        instance._has_proba = hasattr(instance.model, "predict_proba")
        logger.info("Loaded optimized pipeline from %s", path)
        return instance
