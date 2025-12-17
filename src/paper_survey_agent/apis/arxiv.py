"""arXiv API client for retrieving scientific papers."""

import logging
from datetime import datetime
from typing import Optional

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential

from paper_survey_agent.apis.base import BaseScientificAPI
from paper_survey_agent.models.paper import Paper

logger = logging.getLogger(__name__)


class ArxivAPI(BaseScientificAPI):
    """Client for interacting with arXiv API.
    
    Provides methods to search for papers and retrieve detailed information.
    Uses retry logic and timeout handling for robustness.
    """

    def __init__(self, page_size: int = 10, delay_seconds: int = 3):
        """Initialize arXiv API client.
        
        Args:
            page_size: Maximum number of results per search (default: 10)
            delay_seconds: Delay between requests to respect rate limits (default: 3s)
        """
        self.page_size = page_size
        self.delay_seconds = delay_seconds
        self.client = arxiv.Client(
            page_size=page_size,
            delay_seconds=delay_seconds,
            num_retries=3,
        )
        logger.info(f"Initialized ArxivAPI with page_size={page_size}, delay={delay_seconds}s")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
    ) -> list[Paper]:
        """Search arXiv for papers matching the query.
        
        Args:
            query: Search query string (supports arXiv query syntax)
            max_results: Maximum number of papers to return (default: 10)
            sort_by: Sorting criterion (default: Relevance)
            
        Returns:
            List of Paper objects matching the query
            
        Raises:
            arxiv.ArxivError: If the API request fails after retries
        """
        logger.info(f"Searching arXiv: query='{query}', max_results={max_results}")
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by,
            )
            
            results = list(self.client.results(search))
            logger.info(f"Found {len(results)} papers on arXiv")
            
            papers = [self._convert_to_paper(result) for result in results]
            return papers
            
        except Exception as e:
            logger.error(f"arXiv search failed: {e}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_paper_details(self, paper_id: str) -> Paper:
        """Retrieve detailed information for a specific arXiv paper.
        
        Args:
            paper_id: arXiv paper ID (e.g., "2301.12345" or "arXiv:2301.12345")
            
        Returns:
            Paper object with detailed metadata
            
        Raises:
            arxiv.ArxivError: If the paper is not found or API fails
            ValueError: If paper_id format is invalid
        """
        # Normalize paper ID (remove "arXiv:" prefix if present)
        paper_id = paper_id.replace("arXiv:", "").strip()
        logger.info(f"Fetching arXiv paper: {paper_id}")
        
        try:
            search = arxiv.Search(id_list=[paper_id])
            results = list(self.client.results(search))
            
            if not results:
                raise ValueError(f"Paper not found on arXiv: {paper_id}")
            
            paper = self._convert_to_paper(results[0])
            logger.info(f"Retrieved paper: {paper.title}")
            return paper
            
        except Exception as e:
            logger.error(f"Failed to retrieve arXiv paper {paper_id}: {e}", exc_info=True)
            raise

    def _convert_to_paper(self, result: arxiv.Result) -> Paper:
        """Convert arXiv Result object to Paper model.
        
        Args:
            result: arxiv.Result object from API
            
        Returns:
            Paper object with standardized fields
        """
        # Extract arXiv ID (without version)
        arxiv_id = result.entry_id.split("/")[-1].split("v")[0]
        
        # Convert published date to date object
        published_date = result.published.date()
        
        # Extract author names
        authors = [author.name for author in result.authors]
        
        # Extract categories
        categories = result.categories
        
        return Paper(
            id=f"arxiv:{arxiv_id}",
            title=result.title,
            authors=authors,
            abstract=result.summary.replace("\n", " ").strip(),
            published_date=published_date,
            source="arXiv",
            url=result.entry_id,
            pdf_url=result.pdf_url,
            citations_count=None,  # arXiv API doesn't provide citation counts
            categories=categories,
        )
