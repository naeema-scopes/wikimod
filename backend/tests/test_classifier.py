"""Tests for the toxicity classifier."""

from pathlib import Path

import pytest

from app.services.classifier import ToxicityClassifier, ToxicityResult


@pytest.fixture
def classifier(trained_model_dir):
    """Create a classifier using the test-trained model."""
    model_path = Path(trained_model_dir) / "model.pkl"
    vectorizer_path = Path(trained_model_dir) / "vectorizer.pkl"
    return ToxicityClassifier(model_path=model_path, vectorizer_path=vectorizer_path)


def test_scores_toxic_comment(classifier):
    """Obvious toxic text should score high (> 0.7)."""
    result = classifier.predict("you are such an idiot, shut up you moron")
    assert result.score > 0.7
    assert result.is_toxic is True


def test_scores_clean_comment(classifier):
    """Polite text should score low (< 0.3)."""
    result = classifier.predict("thank you for your contribution to this article")
    assert result.score < 0.3
    assert result.is_toxic is False


def test_returns_trigger_words(classifier):
    """Should identify which words contributed to the toxicity score."""
    result = classifier.predict("you are a stupid idiot and a moron")
    assert result.is_toxic is True
    assert len(result.trigger_words) > 0
    # At least one known toxic word should be in trigger words
    trigger_lower = [w.lower() for w in result.trigger_words]
    assert any(w in trigger_lower for w in ["idiot", "stupid", "moron"])


def test_handles_empty_text(classifier):
    """Empty string should return score 0."""
    result = classifier.predict("")
    assert result.score == 0.0
    assert result.is_toxic is False
    assert result.trigger_words == []


def test_handles_whitespace_only(classifier):
    """Whitespace-only string should return score 0."""
    result = classifier.predict("   ")
    assert result.score == 0.0
    assert result.is_toxic is False


def test_batch_prediction(classifier):
    """Batch prediction should score multiple comments at once."""
    texts = [
        "you are an idiot",
        "thank you for your help",
        "shut up you moron",
        "great work on this article",
        "",
    ]
    results = classifier.predict_batch(texts)

    assert len(results) == 5
    assert results[0].is_toxic is True  # toxic
    assert results[1].is_toxic is False  # clean
    assert results[2].is_toxic is True  # toxic
    assert results[3].is_toxic is False  # clean
    assert results[4].score == 0.0  # empty


def test_batch_empty_list(classifier):
    """Empty batch should return empty list."""
    results = classifier.predict_batch([])
    assert results == []


def test_score_range(classifier):
    """All scores should be between 0 and 1."""
    texts = [
        "you are terrible",
        "great discussion",
        "I disagree with this point",
        "this is nonsense",
        "well done editing this section",
    ]
    results = classifier.predict_batch(texts)
    for result in results:
        assert 0.0 <= result.score <= 1.0
