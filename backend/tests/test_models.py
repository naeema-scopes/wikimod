"""Tests for database models and Pydantic schemas."""

import pytest
from datetime import datetime, timezone

from app.models import AnalyzedPage, Comment
from app.schemas import AnalyzeRequest, CommentResponse, HealthScoreResponse


@pytest.mark.asyncio
async def test_create_analyzed_page(db_session):
    """Test creating an AnalyzedPage record."""
    page = AnalyzedPage(
        wikipedia_url="https://en.wikipedia.org/wiki/Python_(programming_language)",
        page_title="Python (programming language)",
        health_score=85.0,
        total_comments=20,
        toxic_count=3,
    )
    db_session.add(page)
    await db_session.commit()
    await db_session.refresh(page)

    assert page.id is not None
    assert page.page_title == "Python (programming language)"
    assert page.health_score == 85.0
    assert page.total_comments == 20
    assert page.toxic_count == 3


@pytest.mark.asyncio
async def test_create_comment(db_session):
    """Test creating a Comment linked to an AnalyzedPage."""
    page = AnalyzedPage(
        wikipedia_url="https://en.wikipedia.org/wiki/Test",
        page_title="Test",
        health_score=70.0,
        total_comments=1,
        toxic_count=1,
    )
    db_session.add(page)
    await db_session.commit()
    await db_session.refresh(page)

    comment = Comment(
        page_id=page.id,
        author="TestUser",
        text="This is a toxic comment",
        timestamp="2024-01-15T10:00:00Z",
        toxicity_score=0.9,
        is_toxic=True,
        trigger_words=["toxic"],
        section_title="Discussion",
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)

    assert comment.id is not None
    assert comment.page_id == page.id
    assert comment.is_toxic is True
    assert comment.trigger_words == ["toxic"]


@pytest.mark.asyncio
async def test_page_comment_relationship(db_session):
    """Test the relationship between AnalyzedPage and Comments."""
    page = AnalyzedPage(
        wikipedia_url="https://en.wikipedia.org/wiki/Test",
        page_title="Test",
        health_score=50.0,
        total_comments=2,
        toxic_count=1,
    )
    db_session.add(page)
    await db_session.commit()
    await db_session.refresh(page)

    c1 = Comment(page_id=page.id, text="Good comment", toxicity_score=0.1, is_toxic=False)
    c2 = Comment(page_id=page.id, text="Bad comment", toxicity_score=0.9, is_toxic=True)
    db_session.add_all([c1, c2])
    await db_session.commit()

    await db_session.refresh(page)
    # Relationship needs explicit loading with async
    from sqlalchemy import select
    from app.models import Comment as CommentModel
    result = await db_session.execute(
        select(CommentModel).where(CommentModel.page_id == page.id)
    )
    comments = result.scalars().all()
    assert len(comments) == 2


def test_analyze_request_valid():
    """Test valid AnalyzeRequest schema."""
    req = AnalyzeRequest(wikipedia_url="https://en.wikipedia.org/wiki/Python")
    assert req.wikipedia_url == "https://en.wikipedia.org/wiki/Python"


def test_analyze_request_invalid_url():
    """Test AnalyzeRequest rejects non-Wikipedia URLs."""
    with pytest.raises(ValueError):
        AnalyzeRequest(wikipedia_url="https://example.com/page")


def test_health_score_response():
    """Test HealthScoreResponse schema."""
    resp = HealthScoreResponse(
        score=85.0,
        total_comments=20,
        toxic_count=3,
        clean_count=17,
        label="Healthy Discussion",
    )
    assert resp.score == 85.0
    assert resp.label == "Healthy Discussion"


def test_comment_response_from_attributes():
    """Test CommentResponse can be created from ORM-like attributes."""
    resp = CommentResponse(
        id="test-id",
        author="User1",
        text="Hello",
        toxicity_score=0.1,
        is_toxic=False,
        trigger_words=[],
    )
    assert resp.id == "test-id"
    assert resp.is_toxic is False
