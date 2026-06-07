"""Shared test fixtures for WikiMod backend tests."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.models import AnalyzedPage, Comment


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
def mock_classifier():
    """Mock toxicity classifier that returns deterministic scores."""

    class MockClassifier:
        TOXIC_PHRASES = [
            "you are stupid", "idiot", "shut up", "go to hell",
            "you're an idiot", "moron", "dumb", "hate you",
        ]

        def predict(self, text: str):
            text_lower = text.lower()
            for phrase in self.TOXIC_PHRASES:
                if phrase in text_lower:
                    return type("Result", (), {
                        "score": 0.9,
                        "is_toxic": True,
                        "trigger_words": [phrase],
                    })()
            return type("Result", (), {
                "score": 0.1,
                "is_toxic": False,
                "trigger_words": [],
            })()

        def predict_batch(self, texts: list[str]):
            return [self.predict(t) for t in texts]

    return MockClassifier()


@pytest.fixture
def trained_model_dir():
    """Train a tiny model on synthetic data for integration tests."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        import joblib
    except ImportError:
        pytest.skip("scikit-learn not available")

    toxic_texts = [
        "you are such an idiot",
        "shut up you moron",
        "I hate you so much",
        "you're stupid and worthless",
        "go to hell",
        "what a dumb comment",
        "you are a terrible person",
        "this is the worst garbage",
        "kill yourself",
        "you disgusting fool",
    ] * 10

    clean_texts = [
        "thank you for your contribution",
        "I agree with your analysis",
        "great work on this article",
        "could you please provide a source",
        "this is a well-written section",
        "I appreciate your perspective",
        "let me add some references",
        "good point about the methodology",
        "welcome to the discussion",
        "the article needs more citations",
    ] * 10

    texts = toxic_texts + clean_texts
    labels = [1] * len(toxic_texts) + [0] * len(clean_texts)

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)
    model = LogisticRegression(max_iter=1000)
    model.fit(X, labels)

    tmpdir = tempfile.mkdtemp()
    model_path = Path(tmpdir) / "model.pkl"
    vectorizer_path = Path(tmpdir) / "vectorizer.pkl"

    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    yield tmpdir

    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
