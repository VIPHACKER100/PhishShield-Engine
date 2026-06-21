import sys
import os
import asyncio
import pytest
from unittest.mock import MagicMock, patch

# Ensure src is in import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.database import SessionLocal, User, Feedback, UsageLog, init_db
from src.models.deep_learning import DeepLearningModel
from src.models.vector_search import VectorSearchDB
from src.models.explainability import get_prediction_explanation
from src.core.worker import check_drift, send_security_alert

def test_database_orm():
    """Test database tables and SQLAlchemy operations."""
    import uuid
    unique = uuid.uuid4().hex[:8]
    uname = f"test_db_{unique}"
    akey = f"key_{unique}"

    init_db()
    session = SessionLocal()
    try:
        # 1. Test User
        user = User(username=uname, password_hash="hash", api_key=akey)
        session.add(user)
        session.commit()
        assert user.id is not None

        db_user = session.query(User).filter_by(username=uname).first()
        assert db_user is not None
        assert db_user.api_key == akey

        # 2. Test UsageLog
        log = UsageLog(user_id=user.id, endpoint="/predict", request_body="{}", response_body="{}")
        session.add(log)
        session.commit()
        assert log.id is not None
        assert log.user.username == uname

        # 3. Test Feedback
        feedback = Feedback(email_text="test text", predicted_label="ham", correct_label="spam", model_used="naive_bayes")
        session.add(feedback)
        session.commit()
        assert feedback.id is not None

        db_feedback = session.query(Feedback).filter_by(id=feedback.id).first()
        assert db_feedback is not None
        assert db_feedback.correct_label == "spam"
    finally:
        # Cleanup test data
        session.rollback()
        session.query(UsageLog).filter_by(user_id=user.id if 'user' in dir() else -1).delete()
        session.query(Feedback).filter_by(id=feedback.id if 'feedback' in dir() else -1).delete()
        session.query(User).filter_by(username=uname).delete()
        session.commit()
        session.close()

def test_deep_learning_mocked():
    """Test DeepLearningModel class with a mocked transformer pipeline."""
    with patch("src.models.deep_learning.pipeline") as mock_pipeline:
        mock_classifier = MagicMock()
        mock_classifier.return_value = [{"label": "phishing", "score": 0.95}]
        mock_pipeline.return_value = mock_classifier
        
        model = DeepLearningModel()
        model.load()
        assert model.is_loaded
        
        res = model.predict("click this phishing link")
        assert res["prediction"] == "spam"
        assert res["confidence"] == 0.95
        assert res["model_used"] == "ealvaradob/bert-finetuned-phishing"

def test_vector_search_mocked():
    """Test VectorSearchDB with mocked ChromaDB and SentenceTransformer."""
    with patch("src.models.vector_search.chromadb.PersistentClient") as mock_client_cls, \
         patch("src.models.vector_search.SentenceTransformer") as mock_transformer_cls:
        
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_cls.return_value = mock_client
        
        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        mock_transformer_cls.return_value = mock_encoder
        
        vdb = VectorSearchDB(db_path="/mock/path")
        vdb.initialize()
        
        # Test add email
        vdb.add_email("doc1", "phishing text", "spam")
        mock_collection.add.assert_called_once()
        
        # Test search similar
        mock_collection.count.return_value = 1
        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["phishing text"]],
            "metadatas": [[{"label": "spam"}]],
            "distances": [[0.123]]
        }
        
        results = vdb.search_similar("similar text", n_results=1)
        assert len(results) == 1
        assert results[0]["id"] == "doc1"
        assert results[0]["distance"] == 0.123

def test_explainability_with_shap():
    """Test explainability layer with and without SHAP/model inputs."""
    # Without model/vectorizer
    explanation = get_prediction_explanation(
        text="normal message",
        prediction="ham",
        security_results={"threat_reasons": [], "risk_level": "LOW"}
    )
    assert explanation["risk_level"] == "LOW"
    assert "Classified as HAM" in explanation["summary"]

    # Mock model and vectorizer
    mock_model = MagicMock()
    mock_vectorizer = MagicMock()
    mock_vectorizer.transform.return_value = "vectorized_text"
    mock_vectorizer.get_feature_names_out.return_value = ["click", "free", "money"]
    
    with patch("src.models.explainability.shap.LinearExplainer") as mock_explainer_cls:
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = [[[0.1, 0.5, 0.0]]]
        mock_explainer_cls.return_value = mock_explainer
        
        explanation = get_prediction_explanation(
            text="free money",
            prediction="spam",
            security_results={"threat_reasons": ["high risk"], "risk_level": "HIGH"},
            model=mock_model,
            vectorizer=mock_vectorizer
        )
        assert explanation["risk_level"] == "HIGH"
        assert len(explanation["shap_analysis"]) > 0

def test_worker_tasks():
    """Test arq background worker tasks with mocks."""
    mock_drift = MagicMock()
    mock_alert = MagicMock()

    async def _run():
        with patch("src.core.worker.drift_monitor.check", mock_drift), \
             patch("src.core.worker.trigger_security_alert", mock_alert):

            await check_drift(None, "email text", "ham")
            mock_drift.assert_called_once_with(["email text"], ["ham"])

            result_dict = {"prediction": "spam", "security_risk_score": 85}
            await send_security_alert(None, "Phishing", result_dict)
            mock_alert.assert_called_once_with("Phishing", result_dict)

    asyncio.run(_run())
