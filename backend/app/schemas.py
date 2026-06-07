"""Pydantic request/response schemas for WikiMod API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    """Request schema for POST /analyze."""

    wikipedia_url: str = Field(..., description="Wikipedia article URL to analyze")

    @field_validator("wikipedia_url")
    @classmethod
    def validate_wikipedia_url(cls, v: str) -> str:
        if "wikipedia.org" not in v.lower():
            raise ValueError("URL must be a Wikipedia article URL")
        return v


class CommentResponse(BaseModel):
    """Response schema for a single analyzed comment."""

    id: str
    author: Optional[str] = None
    text: str
    timestamp: Optional[str] = None
    toxicity_score: float = Field(..., ge=0.0, le=1.0)
    is_toxic: bool
    trigger_words: list[str] = Field(default_factory=list)
    section_title: Optional[str] = None

    model_config = {"from_attributes": True}


class HealthScoreResponse(BaseModel):
    """Health score summary."""

    score: float = Field(..., ge=0.0, le=100.0, description="Health score 0-100")
    total_comments: int
    toxic_count: int
    clean_count: int
    label: str = Field(..., description="Human-readable health label")


class EscalationDataPoint(BaseModel):
    """A single data point in an escalation time series."""

    index: int
    toxicity_score: float
    comment_preview: str = ""
    author: Optional[str] = None


class SectionEscalation(BaseModel):
    """Escalation data for a single talk page section."""

    section_title: str
    trend: str = Field(..., description="escalating, stable, de-escalating, or insufficient_data")
    slope: float = 0.0
    data_points: list[EscalationDataPoint] = Field(default_factory=list)


class EscalationReport(BaseModel):
    """Complete escalation report for a talk page."""

    sections: list[SectionEscalation] = Field(default_factory=list)
    overall_trend: str = "stable"


class AnalysisResponse(BaseModel):
    """Full response for a completed analysis."""

    id: str
    wikipedia_url: str
    page_title: str
    health_score: HealthScoreResponse
    comments: list[CommentResponse] = Field(default_factory=list)
    escalation: Optional[EscalationReport] = None
    scanned_at: datetime

    model_config = {"from_attributes": True}


class HistoryEntry(BaseModel):
    """A single historical scan entry."""

    id: str
    wikipedia_url: str
    page_title: str
    health_score: float
    total_comments: int
    toxic_count: int
    scanned_at: datetime

    model_config = {"from_attributes": True}


class ModelMetrics(BaseModel):
    """Model evaluation metrics."""

    accuracy: float = 0.0
    precision_toxic: float = 0.0
    recall_toxic: float = 0.0
    f1_toxic: float = 0.0
    precision_clean: float = 0.0
    recall_clean: float = 0.0
    f1_clean: float = 0.0
    weighted_f1: float = 0.0
    confusion_matrix: list[list[int]] = Field(default_factory=lambda: [[0, 0], [0, 0]])
    training_samples: int = 0
    note: str = ""


class ModelLimitations(BaseModel):
    """Known limitations of the toxicity model."""

    limitations: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
