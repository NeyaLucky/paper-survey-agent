from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ROOT_DIR: str = str(Path(__file__).parent.parent.parent.resolve())

    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    LLM_API_KEY: str | None = None
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1024

    MAX_PAPERS_TO_RETURN: int = 10
    MAX_RESULTS_PER_SOURCE: int = 10
    MAX_RESULTS_RERANKED: int = MAX_RESULTS_PER_SOURCE * 2
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

    SEMANTIC_SCHOLAR_API_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    SEMANTIC_SCHOLAR_TIMEOUT: int = 60

    DATA_DIR: str = ROOT_DIR + "/data"
    PDF_DOWNLOAD_TIMEOUT: int = 30
    PDF_MAX_CONCURRENT_DOWNLOADS: int = 5
    USER_AGENT: str = "PaperSurveyAgent/1.0"

    LOG_LEVEL: str = "INFO"


settings = Settings()
