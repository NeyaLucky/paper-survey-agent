import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "openai/gpt-oss-120b:free"
    LLM_API_KEY: str | None = None
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1024

    MAX_PAPERS_TO_RETURN: int = 15
    MAX_RESULTS_PER_SOURCE: int = 20
    SEARCH_TIMEOUT: int = 300

    RANKING_FUZZY_THRESHOLD: int = 85

    WEIGHT_RELEVANCE: float = 0.4
    WEIGHT_CITATIONS: float = 0.3
    WEIGHT_RECENCY: float = 0.2
    WEIGHT_PDF_BONUS: float = 0.1

    RECENCY_VERY_RECENT: int = 2
    RECENCY_RECENT: int = 5
    RECENCY_MODERATE: int = 10

    ARXIV_PAGE_SIZE: int = 10
    ARXIV_DELAY_SECONDS: int = 3

    SEMANTIC_SCHOLAR_API_URL: str = "https://api.semanticscholar.org/graph/v1"
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    SEMANTIC_SCHOLAR_TIMEOUT: int = 60

    LOG_LEVEL: str = "INFO"


settings = Settings()
