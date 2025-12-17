"""Semantic Scholar API client for retrieving scientific papers."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from paper_survey_agent.apis.base import BaseScientificAPI
from paper_survey_agent.models.paper import Paper

logger = logging.getLogger(__name__)


class SemanticScholarAPI(BaseScientificAPI):
    """Client for interacting with Semantic Scholar API.

    Provides methods to search for papers and retrieve detailed information.
    Implements rate limiting (1 request per second with API key) and retry logic.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # Rate limit: 1 request per second (for API key holders)
    # Without key: 100 requests per 5 minutes
    RATE_LIMIT_DELAY = 1.0
    
    # Fields to retrieve from API
    PAPER_FIELDS = [
        "paperId",
        "title",
        "abstract",
        "authors",
        "year",
        "publicationDate",
        "url",
        "openAccessPdf",
        "citationCount",
        "fieldsOfStudy",
        "externalIds",
    ]

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        """Initialize Semantic Scholar API client.
        
        Args:
            api_key: Optional API key for higher rate limits (default: None)
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.last_request_time = 0.0
        
        # Set up headers
        headers = {"Accept": "application/json"}
        if api_key:
            headers["x-api-key"] = api_key
            
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=timeout,
        )
        
        logger.info(
            f"Initialized SemanticScholarAPI "
            f"(authenticated: {bool(api_key)}, timeout: {timeout}s)"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close client."""
        await self.client.aclose()

    async def _rate_limit(self):
        """Enforce rate limiting: max 1 request per 3 seconds."""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.RATE_LIMIT_DELAY:
            wait_time = self.RATE_LIMIT_DELAY - time_since_last_request
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = asyncio.get_event_loop().time()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=3, max=10),
        reraise=True,
    )
    async def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """Search Semantic Scholar for papers matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of papers to return (default: 10)
            
        Returns:
            List of Paper objects matching the query
            
        Raises:
            httpx.HTTPError: If the API request fails after retries
        """
        await self._rate_limit()
        
        logger.info(f"Searching Semantic Scholar: query='{query}', max_results={max_results}")
        
        try:
            response = await self.client.get(
                "/paper/search",
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": ",".join(self.PAPER_FIELDS),
                },
            )
            response.raise_for_status()
            
            data = response.json()
            papers_data = data.get("data", [])
            
            logger.info(f"Found {len(papers_data)} papers on Semantic Scholar")
            
            papers = [self._convert_to_paper(paper_data) for paper_data in papers_data]
            return papers
            
        except httpx.HTTPStatusError as e:
            # Handle rate limit error with exponential backoff
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit (429), waiting before retry...")
                await asyncio.sleep(5)
                raise httpx.NetworkError("Rate limit - triggering retry") from e
            logger.error(f"Semantic Scholar API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}", exc_info=True)
            raise

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_paper_details(self, paper_id: str) -> Paper:
        """Retrieve detailed information for a specific Semantic Scholar paper.
        
        Args:
            paper_id: Semantic Scholar paper ID
            
        Returns:
            Paper object with detailed metadata
            
        Raises:
            httpx.HTTPStatusError: If the paper is not found or API fails
            ValueError: If paper_id is invalid
        """
        await self._rate_limit()
        
        if not paper_id:
            raise ValueError("paper_id cannot be empty")
            
        logger.info(f"Fetching Semantic Scholar paper: {paper_id}")
        
        try:
            response = await self.client.get(
                f"/paper/{paper_id}",
                params={"fields": ",".join(self.PAPER_FIELDS)},
            )
            response.raise_for_status()
            
            paper_data = response.json()
            paper = self._convert_to_paper(paper_data)
            
            logger.info(f"Retrieved paper: {paper.title}")
            return paper
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Paper not found on Semantic Scholar: {paper_id}")
            logger.error(f"Semantic Scholar API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve Semantic Scholar paper {paper_id}: {e}", exc_info=True)
            raise

    def _convert_to_paper(self, data: dict) -> Paper:
        """Convert Semantic Scholar JSON response to Paper model.
        
        Args:
            data: JSON data from Semantic Scholar API
            
        Returns:
            Paper object with standardized fields
        """
        paper_id = data.get("paperId", "")
        
        # Extract title
        title = data.get("title", "Unknown Title")
        
        # Extract authors
        authors_data = data.get("authors", [])
        authors = [author.get("name", "Unknown") for author in authors_data]
        
        # Extract abstract
        abstract = data.get("abstract") or "No abstract available"
        
        # Extract publication date
        pub_date_str = data.get("publicationDate") or data.get("year")
        if pub_date_str:
            try:
                if isinstance(pub_date_str, int):
                    # Year only
                    published_date = datetime(pub_date_str, 1, 1).date()
                else:
                    # Full date (YYYY-MM-DD)
                    published_date = datetime.fromisoformat(pub_date_str).date()
            except (ValueError, TypeError):
                published_date = datetime.now().date()
        else:
            published_date = datetime.now().date()
        
        # Extract URL
        url = data.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}"
        
        # Extract PDF URL
        pdf_data = data.get("openAccessPdf")
        pdf_url = pdf_data.get("url") if pdf_data else None
        
        # Extract citation count
        citations_count = data.get("citationCount")
        
        # Extract fields of study (categories)
        categories = data.get("fieldsOfStudy") or []
        
        # Check for arXiv ID
        external_ids = data.get("externalIds") or {}
        arxiv_id = external_ids.get("ArXiv")
        if arxiv_id:
            # If paper is from arXiv, use arXiv ID
            paper_id_final = f"arxiv:{arxiv_id}"
        else:
            paper_id_final = f"s2:{paper_id}"
        
        return Paper(
            id=paper_id_final,
            title=title,
            authors=authors,
            abstract=abstract,
            published_date=published_date,
            source="Semantic Scholar",
            url=url,
            pdf_url=pdf_url,
            citations_count=citations_count,
            categories=categories,
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Closed SemanticScholarAPI client")
