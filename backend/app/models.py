"""SQLAlchemy ORM models for WikiMod."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class AnalyzedPage(Base):
    """Represents a single scan of a Wikipedia talk page."""

    __tablename__ = "analyzed_pages"

    id = Column(String, primary_key=True, default=generate_uuid)
    wikipedia_url = Column(String, nullable=False)
    page_title = Column(String, nullable=False, index=True)
    health_score = Column(Float, nullable=False)  # 0-100 percentage
    total_comments = Column(Integer, nullable=False, default=0)
    toxic_count = Column(Integer, nullable=False, default=0)
    scanned_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    comments = relationship("Comment", back_populates="page", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AnalyzedPage(title='{self.page_title}', score={self.health_score})>"


class Comment(Base):
    """Represents a single comment extracted from a talk page."""

    __tablename__ = "comments"

    id = Column(String, primary_key=True, default=generate_uuid)
    page_id = Column(String, ForeignKey("analyzed_pages.id"), nullable=False)
    author = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    timestamp = Column(String, nullable=True)
    toxicity_score = Column(Float, nullable=False, default=0.0)  # 0-1
    is_toxic = Column(Boolean, nullable=False, default=False)
    trigger_words = Column(JSON, nullable=True, default=list)
    section_title = Column(String, nullable=True)

    page = relationship("AnalyzedPage", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment(author='{self.author}', toxic={self.is_toxic})>"
