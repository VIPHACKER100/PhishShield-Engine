"""Tests for text preprocessing."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.preprocessing.text_cleaner import (
    to_lowercase,
    remove_punctuation,
    remove_numbers,
    remove_stopwords,
    tokenize,
    stem_tokens,
    preprocess_text,
)


def test_to_lowercase():
    assert to_lowercase("HELLO World") == "hello world"


def test_remove_punctuation():
    assert remove_punctuation("Hello, World!") == "Hello World"


def test_remove_numbers():
    assert remove_numbers("Win 1000 dollars") == "Win  dollars"


def test_remove_stopwords():
    tokens = ["this", "is", "a", "test", "email"]
    filtered = remove_stopwords(tokens)
    assert "this" not in filtered
    assert "test" in filtered
    assert "email" in filtered


def test_tokenize():
    assert tokenize("hello world") == ["hello", "world"]


def test_stem_tokens():
    stems = stem_tokens(["running", "played", "happily"])
    assert "run" in stems
    assert "play" in stems


def test_preprocess_text():
    result = preprocess_text("FREE money!! Win $500 NOW")
    assert result  # not empty
    assert "!" not in result
    assert "500" not in result
    # all lowercase
    assert result == result.lower()


def test_preprocess_text_empty():
    result = preprocess_text("")
    assert result == ""
