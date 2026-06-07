"""Tests for analysis API routes."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import Base, get_db
from app.models import AnalyzedPage, Comment
from app.services.analyzer import AnalysisResult


@pytest_asyncio.fixture
async def test_db():
    """Create a test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session_factory

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _mock_analysis_result():
    """Create a mock AnalysisResult."""
    return AnalysisResult(
        page_id="test-page-id",
        wikipedia_url="https://en.wikipedia.org/wiki/Test",
        page_title="Talk:Test",
        health_score=75.0,
        total_comments=4,
        toxic_count=1,
        comments=[
            {
                "author": "Alice",
                "text": "Great article",
                "timestamp": "14:00, 1 January 2024 (UTC)",
                "toxicity_score": 0.1,
                "is_toxic": False,
                "trigger_words": [],
                "section_title": "Quality",
            },
            {
                "author": "Bob",
                "text": "You are an idiot",
                "timestamp": "15:00, 1 January 2024 (UTC)",
                "toxicity_score": 0.9,
                "is_toxic": True,
                "trigger_words": ["idiot"],
                "section_title": "Disputes",
            },
            {
                "author": "Charlie",
                "text": "I agree with Alice",
                "timestamp": "16:00, 1 January 2024 (UTC)",
                "toxicity_score": 0.1,
                "is_toxic": False,
                "trigger_words": [],
                "section_title": "Quality",
            },
            {
                "author": "Dave",
                "text": "Let me add a source",
                "timestamp": "17:00, 1 January 2024 (UTC)",
                "toxicity_score": 0.05,
                "is_toxic": False,
                "trigger_words": [],
                "section_title": "Quality",
            },
        ],
        scanned_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_post_analyze(client):
    """POST /api/analyze with Wikipedia URL returns analysis."""
    mock_result = _mock_analysis_result()

    with patch("app.routers.analyze._get_analysis_service") as mock_service_fn:
        mock_service = MagicMock()
        mock_service.analyze = AsyncMock(return_value=mock_result)
        mock_service_fn.return_value = mock_service

        response = await client.post(
            "/api/analyze",
            json={"wikipedia_url": "https://en.wikipedia.org/wiki/Test"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["page_title"] == "Talk:Test"
    assert data["health_score"]["score"] == 75.0
    assert len(data["comments"]) == 4


@pytest.mark.asyncio
async def test_get_analysis(client, test_db):
    """GET /api/analyze/{id} returns stored analysis."""
    # Insert a page into the test database
    async with test_db() as session:
        page = AnalyzedPage(
            id="test-id-123",
            wikipedia_url="https://en.wikipedia.org/wiki/Test",
            page_title="Talk:Test",
            health_score=80.0,
            total_comments=2,
            toxic_count=0,
        )
        session.add(page)
        comment = Comment(
            page_id="test-id-123",
            author="Alice",
            text="Good comment",
            toxicity_score=0.1,
            is_toxic=False,
            trigger_words=[],
            section_title="General",
        )
        session.add(comment)
        await session.commit()

    response = await client.get("/api/analyze/test-id-123")
    assert response.status_code == 200
    data = response.json()
    assert data["page_title"] == "Talk:Test"
    assert data["health_score"]["score"] == 80.0


@pytest.mark.asyncio
async def test_get_analysis_not_found(client):
    """GET /api/analyze/{id} returns 404 for missing analysis."""
    response = await client.get("/api/analyze/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_url(client):
    """POST /api/analyze returns 422 for non-Wikipedia URLs."""
    response = await client.post(
        "/api/analyze",
        json={"wikipedia_url": "https://example.com/page"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """GET /health returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
