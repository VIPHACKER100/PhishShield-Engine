"""Tests for model training and evaluation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from src.models.train_models import train_model, train_all, split_data, MODEL_REGISTRY
from src.models.evaluate import evaluate_model, evaluate_all


@pytest.fixture
def sample_data():
    """Create a small labelled dataset for testing."""
    texts = [
        "win free money now",
        "claim your prize today",
        "meeting at 3pm tomorrow",
        "please review the document",
        "congratulations you won",
        "quarterly report attached",
        "free gift card click here",
        "project deadline is friday",
    ]
    labels = ["spam", "spam", "ham", "ham", "spam", "ham", "spam", "ham"]
    vec = TfidfVectorizer()
    X = vec.fit_transform(texts)
    return X, labels


def test_split_data(sample_data):
    X, y = sample_data
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.25)
    assert len(y_train) == 6
    assert len(y_test) == 2


def test_train_model_naive_bayes(sample_data):
    X, y = sample_data
    model = train_model(X, y, "naive_bayes")
    pred = model.predict(X[:1])
    assert pred[0] in ("spam", "ham")


def test_train_model_svm(sample_data):
    X, y = sample_data
    model = train_model(X, y, "svm")
    pred = model.predict(X[:1])
    assert pred[0] in ("spam", "ham")


def test_train_model_random_forest(sample_data):
    X, y = sample_data
    model = train_model(X, y, "random_forest")
    pred = model.predict(X[:1])
    assert pred[0] in ("spam", "ham")


def test_train_model_invalid():
    with pytest.raises(ValueError):
        train_model(None, None, "unknown_model")


def test_evaluate_model(sample_data):
    X, y = sample_data
    model = train_model(X, y, "naive_bayes")
    metrics = evaluate_model(model, X, y, "naive_bayes")
    assert "accuracy" in metrics
    assert "f1_score" in metrics
    assert 0 <= metrics["accuracy"] <= 1


def test_evaluate_all(sample_data, tmp_path):
    X, y = sample_data
    models = {}
    for name in MODEL_REGISTRY:
        models[name] = train_model(X, y, name)
    report = evaluate_all(models, X, y, str(tmp_path / "metrics.json"))
    assert "best_model" in report
    assert len(report["results"]) == len(MODEL_REGISTRY)
