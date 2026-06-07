"""History API routes.

GET /history: List all analyzed pages
GET /history/{page_title}: Historical scans for a specific page
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AnalyzedPage
from app.schemas import HistoryEntry

router = APIRouter()


@router.get("/history", response_model=list[HistoryEntry])
async def get_history(
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all analyzed pages, most recent first."""
    stmt = (
        select(AnalyzedPage)
        .order_by(AnalyzedPage.scanned_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    pages = result.scalars().all()

    return [
        HistoryEntry(
            id=p.id,
            wikipedia_url=p.wikipedia_url,
            page_title=p.page_title,
            health_score=p.health_score,
            total_comments=p.total_comments,
            toxic_count=p.toxic_count,
            scanned_at=p.scanned_at,
        )
        for p in pages
    ]


@router.get("/history/{page_title}", response_model=list[HistoryEntry])
async def get_page_history(
    page_title: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all historical scans for a specific page title."""
    stmt = (
        select(AnalyzedPage)
        .where(AnalyzedPage.page_title == page_title)
        .order_by(AnalyzedPage.scanned_at.desc())
    )
    result = await db.execute(stmt)
    pages = result.scalars().all()

    return [
        HistoryEntry(
            id=p.id,
            wikipedia_url=p.wikipedia_url,
            page_title=p.page_title,
            health_score=p.health_score,
            total_comments=p.total_comments,
            toxic_count=p.toxic_count,
            scanned_at=p.scanned_at,
        )
        for p in pages
    ]
