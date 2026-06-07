"""Tests for the analysis orchestrator."""

import pytest
import pytest_asyncio

from app.services.analyzer import AnalysisService
from app.services.wikipedia import WikipediaClient, TalkPageData, CommentData


class FakeWikipediaClient:
    """Fake Wikipedia client that returns predetermined data."""

    def __init__(self, talk_page_data: TalkPageData):
        self._data = talk_page_data

    async def fetch_talk_page(self, url: str) -> TalkPageData:
        return self._data


@pytest.mark.asyncio
async def test_full_analysis_flow(mock_classifier):
    """Given a Wikipedia URL, returns complete analysis with health score and scored comments."""
    comments = [
        CommentData(author="Alice", text="This is a great article", section_title="Quality"),
        CommentData(author="Bob", text="You are stupid and an idiot", section_title="Disputes"),
        CommentData(author="Charlie", text="I agree with Alice", section_title="Quality"),
        CommentData(author="Dave", text="Shut up you moron", section_title="Disputes"),
        CommentData(author="Eve", text="Could you provide a source", section_title="Quality"),
    ]
    fake_client = FakeWikipediaClient(TalkPageData(
        title="Talk:Test Article",
        url="https://en.wikipedia.org/wiki/Test_Article",
        comments=comments,
    ))

    service = AnalysisService(
        wikipedia_client=fake_client,
        classifier=mock_classifier,
    )

    result = await service.analyze("https://en.wikipedia.org/wiki/Test_Article")

    assert result.error is None
    assert result.page_title == "Talk:Test Article"
    assert result.total_comments == 5
    assert result.toxic_count == 2  # "idiot" and "moron" detected
    assert len(result.comments) == 5


@pytest.mark.asyncio
async def test_health_score_calculation(mock_classifier):
    """Health score should be correct percentage of non-toxic comments."""
    # 2 out of 4 comments are toxic => 50% health
    comments = [
        CommentData(author="A", text="Good work", section_title="General"),
        CommentData(author="B", text="You are an idiot", section_title="General"),
        CommentData(author="C", text="Nice article", section_title="General"),
        CommentData(author="D", text="Shut up moron", section_title="General"),
    ]
    fake_client = FakeWikipediaClient(TalkPageData(
        title="Talk:Test",
        url="https://en.wikipedia.org/wiki/Test",
        comments=comments,
    ))

    service = AnalysisService(wikipedia_client=fake_client, classifier=mock_classifier)
    result = await service.analyze("https://en.wikipedia.org/wiki/Test")

    assert result.health_score == 50.0
    assert result.toxic_count == 2
    assert result.total_comments == 4


@pytest.mark.asyncio
async def test_empty_talk_page(mock_classifier):
    """A talk page with no comments should have 100% health score."""
    fake_client = FakeWikipediaClient(TalkPageData(
        title="Talk:Empty",
        url="https://en.wikipedia.org/wiki/Empty",
        comments=[],
    ))

    service = AnalysisService(wikipedia_client=fake_client, classifier=mock_classifier)
    result = await service.analyze("https://en.wikipedia.org/wiki/Empty")

    assert result.health_score == 100.0
    assert result.total_comments == 0
    assert result.toxic_count == 0


@pytest.mark.asyncio
async def test_error_handling(mock_classifier):
    """Should handle errors from the Wikipedia client gracefully."""
    fake_client = FakeWikipediaClient(TalkPageData(
        title="Talk:Error",
        url="https://en.wikipedia.org/wiki/Error",
        error="Talk page not found",
    ))

    service = AnalysisService(wikipedia_client=fake_client, classifier=mock_classifier)
    result = await service.analyze("https://en.wikipedia.org/wiki/Error")

    assert result.error is not None
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_analysis_with_db(mock_classifier, db_session):
    """Analysis should persist results to the database."""
    comments = [
        CommentData(author="A", text="Great work here", section_title="General"),
        CommentData(author="B", text="You are an idiot", section_title="General"),
    ]
    fake_client = FakeWikipediaClient(TalkPageData(
        title="Talk:Persisted",
        url="https://en.wikipedia.org/wiki/Persisted",
        comments=comments,
    ))

    service = AnalysisService(wikipedia_client=fake_client, classifier=mock_classifier)
    result = await service.analyze("https://en.wikipedia.org/wiki/Persisted", db=db_session)

    assert result.page_id != ""
    assert result.total_comments == 2

    # Verify data was stored
    from sqlalchemy import select
    from app.models import AnalyzedPage
    stmt = select(AnalyzedPage).where(AnalyzedPage.id == result.page_id)
    db_result = await db_session.execute(stmt)
    page = db_result.scalar_one()
    assert page.page_title == "Talk:Persisted"
    assert page.health_score == 50.0
