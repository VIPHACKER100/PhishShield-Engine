"""Tests for vectorizer module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from src.features.vectorizer import get_vectorizer, fit_and_save, load_vectorizer


def test_get_vectorizer_tfidf():
    vec = get_vectorizer("tfidf")
    assert isinstance(vec, TfidfVectorizer)


def test_get_vectorizer_bow():
    vec = get_vectorizer("bow")
    assert isinstance(vec, CountVectorizer)


def test_get_vectorizer_invalid():
    with pytest.raises(ValueError):
        get_vectorizer("unknown")


def test_fit_and_save_and_load(tmp_path):
    corpus = ["hello world", "foo bar baz", "hello foo"]
    path = str(tmp_path / "vec.pkl")
    vec, X = fit_and_save(corpus, method="tfidf", path=path)
    assert X.shape[0] == 3
    assert os.path.exists(path)

    loaded = load_vectorizer(path)
    X2 = loaded.transform(["hello world"])
    assert X2.shape[0] == 1
