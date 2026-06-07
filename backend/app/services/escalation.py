"""Conversation escalation detection for talk page sections.

Analyzes toxicity score trends within each talk page section to identify
whether discussions are escalating, stable, or de-escalating.

Algorithm:
- Group comments by section
- For each section with at least 5 comments, compute the linear regression
  slope of toxicity scores vs. comment index
- slope > 0.05 = escalating
- slope < -0.05 = de-escalating
- otherwise = stable
- Sections with < 5 comments are "insufficient_data"
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from app.schemas import SectionEscalation, EscalationDataPoint, EscalationReport


MIN_COMMENTS_FOR_ANALYSIS = 5
ESCALATION_THRESHOLD = 0.05
DE_ESCALATION_THRESHOLD = -0.05


@dataclass
class ScoredComment:
    """A comment with its toxicity score."""

    text: str = ""
    author: Optional[str] = None
    toxicity_score: float = 0.0
    section_title: str = "General"
    timestamp: Optional[str] = None


class EscalationDetector:
    """Detects escalation/de-escalation patterns in talk page discussions."""

    def analyze(self, comments: list[ScoredComment]) -> EscalationReport:
        """Analyze escalation patterns across all sections.

        Args:
            comments: List of scored comments from a talk page.

        Returns:
            EscalationReport with per-section trends and overall assessment.
        """
        if not comments:
            return EscalationReport(sections=[], overall_trend="stable")

        # Group by section
        sections: dict[str, list[ScoredComment]] = {}
        for comment in comments:
            section = comment.section_title or "General"
            if section not in sections:
                sections[section] = []
            sections[section].append(comment)

        # Analyze each section
        section_results = []
        for section_title, section_comments in sections.items():
            result = self._analyze_section(section_title, section_comments)
            section_results.append(result)

        # Determine overall trend
        overall_trend = self._compute_overall_trend(section_results)

        return EscalationReport(
            sections=section_results,
            overall_trend=overall_trend,
        )

    def _analyze_section(
        self, section_title: str, comments: list[ScoredComment]
    ) -> SectionEscalation:
        """Analyze escalation trend for a single section."""
        data_points = [
            EscalationDataPoint(
                index=i,
                toxicity_score=c.toxicity_score,
                comment_preview=c.text[:100] if c.text else "",
                author=c.author,
            )
            for i, c in enumerate(comments)
        ]

        if len(comments) < MIN_COMMENTS_FOR_ANALYSIS:
            return SectionEscalation(
                section_title=section_title,
                trend="insufficient_data",
                slope=0.0,
                data_points=data_points,
            )

        # Linear regression: toxicity_score vs. comment index
        scores = [c.toxicity_score for c in comments]
        indices = list(range(len(scores)))

        slope = self._linear_regression_slope(indices, scores)

        if slope > ESCALATION_THRESHOLD:
            trend = "escalating"
        elif slope < DE_ESCALATION_THRESHOLD:
            trend = "de-escalating"
        else:
            trend = "stable"

        return SectionEscalation(
            section_title=section_title,
            trend=trend,
            slope=round(slope, 4),
            data_points=data_points,
        )

    @staticmethod
    def _linear_regression_slope(x: list[int], y: list[float]) -> float:
        """Compute the slope of a simple linear regression."""
        n = len(x)
        if n < 2:
            return 0.0

        x_arr = np.array(x, dtype=float)
        y_arr = np.array(y, dtype=float)

        x_mean = np.mean(x_arr)
        y_mean = np.mean(y_arr)

        numerator = np.sum((x_arr - x_mean) * (y_arr - y_mean))
        denominator = np.sum((x_arr - x_mean) ** 2)

        if denominator == 0:
            return 0.0

        return float(numerator / denominator)

    @staticmethod
    def _compute_overall_trend(sections: list[SectionEscalation]) -> str:
        """Compute the overall trend across all sections."""
        analyzable = [s for s in sections if s.trend != "insufficient_data"]
        if not analyzable:
            return "stable"

        escalating = sum(1 for s in analyzable if s.trend == "escalating")
        de_escalating = sum(1 for s in analyzable if s.trend == "de-escalating")

        if escalating > de_escalating:
            return "escalating"
        elif de_escalating > escalating:
            return "de-escalating"
        return "stable"
