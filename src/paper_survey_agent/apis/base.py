"""Base abstract class for scientific API clients."""

from abc import ABC, abstractmethod

from paper_survey_agent.models.paper import Paper


class BaseScientificAPI(ABC):
    """Abstract base class for scientific paper API clients."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[Paper]:
        """Search for papers matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of papers to return (default: 10)
            
        Returns:
            List of Paper objects matching the query
            
        Raises:
            Exception: Implementation-specific errors (network, API, etc.)
        """
        pass

    @abstractmethod
    async def get_paper_details(self, paper_id: str) -> Paper:
        """Retrieve detailed information for a specific paper.
        
        Args:
            paper_id: Paper identifier (format depends on the API)
            
        Returns:
            Paper object with detailed metadata
            
        Raises:
            ValueError: If paper_id format is invalid
            Exception: Implementation-specific errors (network, API, etc.)
        """
        pass
