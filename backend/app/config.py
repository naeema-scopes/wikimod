"""Application configuration using pydantic-settings."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./wikimod.db"
    model_path: Path = Path(__file__).parent / "ml" / "model.pkl"
    vectorizer_path: Path = Path(__file__).parent / "ml" / "vectorizer.pkl"
    metrics_path: Path = Path(__file__).parent / "ml" / "metrics.json"

    # MediaWiki API settings
    wikipedia_api_user_agent: str = "WikiMod/0.1.0 (toxicity monitor; contact@example.com)"

    # Rate limiting
    rate_limit: str = "5/minute"

    model_config = {"env_prefix": "WIKIMOD_", "env_file": ".env"}


settings = Settings()
