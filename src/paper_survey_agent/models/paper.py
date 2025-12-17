from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field


class Paper(BaseModel):
    id: str = Field(..., description="Unique identifier (DOI or arXiv ID)")
    title: str = Field(..., description="Title of the publication")
    authors: list[str] = Field(..., description="List of author names")
    abstract: str = Field(..., description="Abstract/summary of the paper")
    published_date: date = Field(..., description="Publication date")
    source: str = Field(..., description="Source of the paper (arxiv, semantic_scholar)")
    url: str = Field(..., description="URL to the paper")
    pdf_url: str | None = Field(default=None, description="URL to PDF if available")
    citations_count: int | None = Field(default=None, description="Number of citations")
    categories: list[str] = Field(default_factory=list, description="Categories/tags of the paper")


class ProcessedPaper(Paper):
    pdf_path: Path | None = Field(default=None, description="Local filesystem path to the downloaded PDF")
    txt_path: Path | None = Field(default=None, description="Local filesystem path to the extracted text content")
