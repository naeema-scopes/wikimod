"""Analysis API routes.

POST /analyze: Submit a Wikipedia URL for toxicity analysis
GET /analyze/{id}: Retrieve a stored analysis by ID
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import AnalyzedPage, Comment
from app.schemas import (
    AnalyzeRequest,
    AnalysisResponse,
    CommentResponse,
    HealthScoreResponse,
    EscalationReport,
)
from app.services.analyzer import AnalysisService
from app.services.escalation import EscalationDetector, ScoredComment
from app.services.wikipedia import WikipediaClient

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Lazy-loaded singleton
_analysis_service: Optional[AnalysisService] = None


def _get_analysis_service() -> AnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service


def _health_label(score: float) -> str:
    """Get human-readable label for a health score."""
    if score >= 80:
        return "Healthy Discussion"
    elif score >= 50:
        return "Some Concerns"
    return "Hostile Environment"


@router.post("/analyze", response_model=AnalysisResponse)
@limiter.limit("5/minute")
async def analyze_page(
    request: Request,
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze a Wikipedia talk page for toxicity.

    Rate limited to 5 requests per minute per IP.
    """
    service = _get_analysis_service()

    # Run analysis (classifier inference is CPU-bound, use thread pool)
    loop = asyncio.get_event_loop()
    result = await service.analyze(body.wikipedia_url, db=db)

    if result.error:
        raise HTTPException(status_code=404, detail=result.error)

    # Run escalation detection
    scored_comments = [
        ScoredComment(
            text=c["text"],
            author=c["author"],
            toxicity_score=c["toxicity_score"],
            section_title=c["section_title"],
        )
        for c in result.comments
    ]
    detector = EscalationDetector()
    escalation = detector.analyze(scored_comments)

    comments = [
        CommentResponse(
            id=f"c-{i}",
            author=c["author"],
            text=c["text"],
            timestamp=c["timestamp"],
            toxicity_score=c["toxicity_score"],
            is_toxic=c["is_toxic"],
            trigger_words=c["trigger_words"],
            section_title=c["section_title"],
        )
        for i, c in enumerate(result.comments)
    ]

    return AnalysisResponse(
        id=result.page_id,
        wikipedia_url=result.wikipedia_url,
        page_title=result.page_title,
        health_score=HealthScoreResponse(
            score=result.health_score,
            total_comments=result.total_comments,
            toxic_count=result.toxic_count,
            clean_count=result.total_comments - result.toxic_count,
            label=_health_label(result.health_score),
        ),
        comments=comments,
        escalation=escalation,
        scanned_at=result.scanned_at,
    )


@router.get("/analyze/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a stored analysis by ID."""
    stmt = select(AnalyzedPage).where(AnalyzedPage.id == analysis_id)
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Load comments
    comments_stmt = select(Comment).where(Comment.page_id == page.id)
    comments_result = await db.execute(comments_stmt)
    db_comments = comments_result.scalars().all()

    comments = [
        CommentResponse(
            id=c.id,
            author=c.author,
            text=c.text,
            timestamp=c.timestamp,
            toxicity_score=c.toxicity_score,
            is_toxic=c.is_toxic,
            trigger_words=c.trigger_words or [],
            section_title=c.section_title,
        )
        for c in db_comments
    ]

    # Re-run escalation detection on stored comments
    scored_comments = [
        ScoredComment(
            text=c.text,
            author=c.author,
            toxicity_score=c.toxicity_score,
            section_title=c.section_title or "General",
        )
        for c in db_comments
    ]
    detector = EscalationDetector()
    escalation = detector.analyze(scored_comments)

    return AnalysisResponse(
        id=page.id,
        wikipedia_url=page.wikipedia_url,
        page_title=page.page_title,
        health_score=HealthScoreResponse(
            score=page.health_score,
            total_comments=page.total_comments,
            toxic_count=page.toxic_count,
            clean_count=page.total_comments - page.toxic_count,
            label=_health_label(page.health_score),
        ),
        comments=comments,
        escalation=escalation,
        scanned_at=page.scanned_at,
    )
