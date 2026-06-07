"""Tests for history API routes."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import Base, get_db
from app.models import AnalyzedPage


@pytest_asyncio.fixture
async def test_db():
    """Create a test database with sample history data."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Populate with test data
    async with session_factory() as session:
        pages = [
            AnalyzedPage(
                id=f"page-{i}",
                wikipedia_url=f"https://en.wikipedia.org/wiki/Article_{i % 2}",
                page_title=f"Talk:Article {i % 2}",
                health_score=80.0 + i,
                total_comments=10 + i,
                toxic_count=i,
                scanned_at=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
            )
            for i in range(5)
        ]
        session.add_all(pages)
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield session_factory
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_history(client):
    """GET /api/history returns all scans."""
    response = await client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    # Should be ordered by scanned_at desc
    assert data[0]["id"] == "page-4"


@pytest.mark.asyncio
async def test_get_page_history(client):
    """GET /api/history/{page_title} returns scans for that page."""
    response = await client.get("/api/history/Talk:Article 0")
    assert response.status_code == 200
    data = response.json()
    # Articles 0, 2, 4 have title "Talk:Article 0"
    assert len(data) == 3
    for entry in data:
        assert entry["page_title"] == "Talk:Article 0"


@pytest.mark.asyncio
async def test_get_page_history_empty(client):
    """GET /api/history/{page_title} returns empty for unknown page."""
    response = await client.get("/api/history/Talk:Nonexistent")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_model_metrics(client):
    """GET /api/model/metrics returns model metrics."""
    response = await client.get("/api/model/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "weighted_f1" in data


@pytest.mark.asyncio
async def test_get_model_limitations(client):
    """GET /api/model/limitations returns known limitations."""
    response = await client.get("/api/model/limitations")
    assert response.status_code == 200
    data = response.json()
    assert "limitations" in data
    assert len(data["limitations"]) > 0
    assert "references" in data
