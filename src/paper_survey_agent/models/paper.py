"""Paper model for scientific publications."""

from datetime import date
from pydantic import BaseModel, Field


class Paper(BaseModel):
    """Represents a scientific paper from various sources."""
    
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
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "arxiv:2301.00001",
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "abstract": "The dominant sequence transduction models...",
                "published_date": "2017-06-12",
                "source": "arxiv",
                "url": "https://arxiv.org/abs/1706.03762",
                "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
                "citations_count": 50000,
                "categories": ["cs.CL", "cs.LG"]
            }
        }
