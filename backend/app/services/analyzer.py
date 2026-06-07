"""Analysis orchestrator connecting Wikipedia fetching and toxicity classification.

Coordinates the full analysis flow:
1. Fetch talk page via WikipediaClient
2. Parse into comments
3. Score each comment via ToxicityClassifier
4. Calculate page health score
5. Store results in database
6. Return full analysis
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnalyzedPage, Comment
from app.services.classifier import ToxicityClassifier, ToxicityResult
from app.services.wikipedia import WikipediaClient, TalkPageData


class AnalysisResult:
    """Result of a full talk page analysis."""

    def __init__(
        self,
        page_id: str,
        wikipedia_url: str,
        page_title: str,
        health_score: float,
        total_comments: int,
        toxic_count: int,
        comments: list[dict],
        scanned_at: datetime,
        error: Optional[str] = None,
    ):
        self.page_id = page_id
        self.wikipedia_url = wikipedia_url
        self.page_title = page_title
        self.health_score = health_score
        self.total_comments = total_comments
        self.toxic_count = toxic_count
        self.comments = comments
        self.scanned_at = scanned_at
        self.error = error


class AnalysisService:
    """Orchestrates the full analysis pipeline."""

    def __init__(
        self,
        wikipedia_client: Optional[WikipediaClient] = None,
        classifier: Optional[ToxicityClassifier] = None,
    ):
        self.wikipedia_client = wikipedia_client or WikipediaClient()
        self.classifier = classifier

    def _get_classifier(self) -> ToxicityClassifier:
        """Lazy-load classifier to avoid loading model on import."""
        if self.classifier is None:
            self.classifier = ToxicityClassifier()
        return self.classifier

    async def analyze(
        self,
        url: str,
        db: Optional[AsyncSession] = None,
    ) -> AnalysisResult:
        """Run a full analysis of a Wikipedia talk page.

        Args:
            url: Wikipedia article URL.
            db: Optional database session for persistence.

        Returns:
            AnalysisResult with health score and scored comments.
        """
        # Step 1: Fetch talk page
        talk_page = await self.wikipedia_client.fetch_talk_page(url)

        if talk_page.error:
            return AnalysisResult(
                page_id="",
                wikipedia_url=url,
                page_title=talk_page.title or "Unknown",
                health_score=0.0,
                total_comments=0,
                toxic_count=0,
                comments=[],
                scanned_at=datetime.now(timezone.utc),
                error=talk_page.error,
            )

        if not talk_page.comments:
            return AnalysisResult(
                page_id="",
                wikipedia_url=url,
                page_title=talk_page.title,
                health_score=100.0,
                total_comments=0,
                toxic_count=0,
                comments=[],
                scanned_at=datetime.now(timezone.utc),
            )

        # Step 2: Score each comment
        classifier = self._get_classifier()
        texts = [c.text for c in talk_page.comments]
        results = classifier.predict_batch(texts)

        # Step 3: Build scored comments
        scored_comments = []
        toxic_count = 0

        for comment_data, toxicity_result in zip(talk_page.comments, results):
            if toxicity_result.is_toxic:
                toxic_count += 1
            scored_comments.append({
                "author": comment_data.author,
                "text": comment_data.text,
                "timestamp": comment_data.timestamp,
                "toxicity_score": toxicity_result.score,
                "is_toxic": toxicity_result.is_toxic,
                "trigger_words": toxicity_result.trigger_words,
                "section_title": comment_data.section_title,
            })

        # Step 4: Calculate health score
        total = len(scored_comments)
        health_score = ((total - toxic_count) / total * 100) if total > 0 else 100.0

        # Step 5: Store in database
        scanned_at = datetime.now(timezone.utc)
        page_id = ""

        if db is not None:
            page = AnalyzedPage(
                wikipedia_url=url,
                page_title=talk_page.title,
                health_score=health_score,
                total_comments=total,
                toxic_count=toxic_count,
                scanned_at=scanned_at,
            )
            db.add(page)
            await db.flush()
            page_id = page.id

            for sc in scored_comments:
                comment = Comment(
                    page_id=page.id,
                    author=sc["author"],
                    text=sc["text"],
                    timestamp=sc["timestamp"],
                    toxicity_score=sc["toxicity_score"],
                    is_toxic=sc["is_toxic"],
                    trigger_words=sc["trigger_words"],
                    section_title=sc["section_title"],
                )
                db.add(comment)

            await db.commit()
            await db.refresh(page)
            page_id = page.id

        return AnalysisResult(
            page_id=page_id,
            wikipedia_url=url,
            page_title=talk_page.title,
            health_score=round(health_score, 2),
            total_comments=total,
            toxic_count=toxic_count,
            comments=scored_comments,
            scanned_at=scanned_at,
        )
