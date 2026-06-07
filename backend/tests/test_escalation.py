"""Tests for conversation escalation detection."""

import pytest

from app.services.escalation import EscalationDetector, ScoredComment


@pytest.fixture
def detector():
    return EscalationDetector()


def _make_comments(scores: list[float], section: str = "Test Section") -> list[ScoredComment]:
    """Helper to create scored comments with given toxicity scores."""
    return [
        ScoredComment(
            text=f"Comment {i}",
            author=f"User{i}",
            toxicity_score=score,
            section_title=section,
        )
        for i, score in enumerate(scores)
    ]


def test_detects_escalation(detector):
    """Conversation where toxicity scores increase over time should be flagged."""
    # Steadily increasing toxicity
    scores = [0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]
    comments = _make_comments(scores)

    report = detector.analyze(comments)

    assert len(report.sections) == 1
    section = report.sections[0]
    assert section.trend == "escalating"
    assert section.slope > 0.05


def test_detects_stable(detector):
    """Conversation with consistent low scores should be stable."""
    scores = [0.1, 0.12, 0.09, 0.11, 0.1, 0.13, 0.08]
    comments = _make_comments(scores)

    report = detector.analyze(comments)

    section = report.sections[0]
    assert section.trend == "stable"
    assert abs(section.slope) <= 0.05


def test_detects_de_escalation(detector):
    """Conversation that starts toxic but improves should be flagged."""
    scores = [0.9, 0.8, 0.7, 0.5, 0.3, 0.2, 0.1]
    comments = _make_comments(scores)

    report = detector.analyze(comments)

    section = report.sections[0]
    assert section.trend == "de-escalating"
    assert section.slope < -0.05


def test_per_section_analysis(detector):
    """Returns escalation data grouped by talk page section."""
    comments = (
        _make_comments([0.1, 0.2, 0.3, 0.5, 0.7, 0.9], section="Heated Debate")
        + _make_comments([0.1, 0.1, 0.1, 0.1, 0.1, 0.1], section="Calm Discussion")
    )

    report = detector.analyze(comments)

    assert len(report.sections) == 2

    heated = next(s for s in report.sections if s.section_title == "Heated Debate")
    calm = next(s for s in report.sections if s.section_title == "Calm Discussion")

    assert heated.trend == "escalating"
    assert calm.trend == "stable"


def test_insufficient_data(detector):
    """Sections with fewer than 5 comments should be 'insufficient_data'."""
    scores = [0.1, 0.5, 0.9]  # Only 3 comments
    comments = _make_comments(scores)

    report = detector.analyze(comments)

    section = report.sections[0]
    assert section.trend == "insufficient_data"


def test_empty_comments(detector):
    """Empty comment list should return empty report."""
    report = detector.analyze([])

    assert len(report.sections) == 0
    assert report.overall_trend == "stable"


def test_overall_trend(detector):
    """Overall trend should reflect the majority of sections."""
    comments = (
        _make_comments([0.1, 0.3, 0.5, 0.7, 0.9], section="Section A")
        + _make_comments([0.1, 0.3, 0.5, 0.7, 0.9], section="Section B")
        + _make_comments([0.5, 0.5, 0.5, 0.5, 0.5], section="Section C")
    )

    report = detector.analyze(comments)

    # 2 escalating, 1 stable => overall escalating
    assert report.overall_trend == "escalating"
