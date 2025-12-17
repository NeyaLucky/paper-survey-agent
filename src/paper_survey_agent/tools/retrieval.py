"""Paper retrieval tool for fetching papers from multiple sources."""

import asyncio
import logging
from typing import Optional

from paper_survey_agent.apis import ArxivAPI, SemanticScholarAPI
from paper_survey_agent.models.paper import Paper

logger = logging.getLogger(__name__)


async def retrieve_papers(
    query: str,
    sources: Optional[list[str]] = None,
    max_results_per_source: int = 20,
    semantic_scholar_api_key: Optional[str] = None,
) -> list[Paper]:
    """Retrieve papers from multiple scientific sources in parallel.
    
    Fetches papers from arXiv and Semantic Scholar APIs concurrently,
    combines results, and handles errors gracefully. If one API fails,
    the function continues and returns results from the other source.
    
    Args:
        query: Search query string
        sources: List of sources to query (default: ["arxiv", "semantic_scholar"])
                 Available: "arxiv", "semantic_scholar"
        max_results_per_source: Maximum papers to fetch from each source (default: 20)
        semantic_scholar_api_key: Optional API key for Semantic Scholar (default: None)
        
    Returns:
        Combined list of Paper objects from all successful sources
        
    Raises:
        ValueError: If all sources fail to return results
        
    """
    # Default to all sources if not specified
    if sources is None:
        sources = ["arxiv", "semantic_scholar"]
    
    # Normalize source names (case-insensitive)
    sources = [s.lower().strip() for s in sources]
    
    logger.info(
        f"Retrieving papers: query='{query}', sources={sources}, "
        f"max_per_source={max_results_per_source}"
    )
    
    # Create tasks for parallel API calls
    tasks = []
    
    if "arxiv" in sources:
        tasks.append(_fetch_from_arxiv(query, max_results_per_source))
    
    if "semantic_scholar" in sources or "semantic-scholar" in sources or "s2" in sources:
        tasks.append(_fetch_from_semantic_scholar(query, max_results_per_source, semantic_scholar_api_key))
    
    if not tasks:
        raise ValueError(f"No valid sources specified. Available: arxiv, semantic_scholar. Got: {sources}")
    
    # Execute all API calls in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine successful results
    all_papers = []
    successful_sources = []
    failed_sources = []
    
    for i, result in enumerate(results):
        source_name = sources[i] if i < len(sources) else "unknown"
        
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch from {source_name}: {result}", exc_info=result)
            failed_sources.append(source_name)
        elif isinstance(result, list):
            all_papers.extend(result)
            successful_sources.append(source_name)
            logger.info(f"Retrieved {len(result)} papers from {source_name}")
        else:
            logger.warning(f"Unexpected result type from {source_name}: {type(result)}")
            failed_sources.append(source_name)
    
    # Log summary
    logger.info(
        f"Retrieval complete: {len(all_papers)} total papers from {len(successful_sources)} sources. "
        f"Successful: {successful_sources}, Failed: {failed_sources}"
    )
    
    # Raise error if all sources failed
    if not all_papers:
        raise ValueError(
            f"Failed to retrieve papers from all sources. "
            f"Attempted: {sources}, Failed: {failed_sources}"
        )
    
    return all_papers


async def _fetch_from_arxiv(query: str, max_results: int) -> list[Paper]:
    """Fetch papers from arXiv API.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of Paper objects from arXiv
        
    Raises:
        Exception: If arXiv API call fails
    """
    logger.debug(f"Fetching from arXiv: query='{query}', max_results={max_results}")
    
    try:
        api = ArxivAPI()
        papers = await api.search(query, max_results=max_results)
        logger.info(f"arXiv returned {len(papers)} papers")
        return papers
    except Exception as e:
        logger.error(f"arXiv API error: {e}", exc_info=True)
        raise


async def _fetch_from_semantic_scholar(
    query: str,
    max_results: int,
    api_key: Optional[str] = None,
) -> list[Paper]:
    """Fetch papers from Semantic Scholar API.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        api_key: Optional API key for higher rate limits
        
    Returns:
        List of Paper objects from Semantic Scholar
        
    Raises:
        Exception: If Semantic Scholar API call fails
    """
    logger.debug(
        f"Fetching from Semantic Scholar: query='{query}', "
        f"max_results={max_results}, authenticated={bool(api_key)}"
    )
    
    try:
        async with SemanticScholarAPI(api_key=api_key) as api:
            papers = await api.search(query, max_results=max_results)
            logger.info(f"Semantic Scholar returned {len(papers)} papers")
            return papers
    except Exception as e:
        logger.error(f"Semantic Scholar API error: {e}", exc_info=True)
        raise


async def retrieve_papers_batch(
    queries: list[str],
    sources: Optional[list[str]] = None,
    max_results_per_query: int = 10,
    semantic_scholar_api_key: Optional[str] = None,
) -> dict[str, list[Paper]]:
    """Retrieve papers for multiple queries in parallel.
    
    Useful for the planning stage where LLM generates multiple search queries.
    
    Args:
        queries: List of search queries
        sources: List of sources to query (default: ["arxiv", "semantic_scholar"])
        max_results_per_query: Maximum papers per query (default: 10)
        semantic_scholar_api_key: Optional API key for Semantic Scholar
        
    Returns:
        Dictionary mapping each query to its list of papers
    """
    logger.info(f"Batch retrieval: {len(queries)} queries, max {max_results_per_query} per query")
    
    # Create tasks for all queries
    tasks = [
        retrieve_papers(
            query=query,
            sources=sources,
            max_results_per_source=max_results_per_query,
            semantic_scholar_api_key=semantic_scholar_api_key,
        )
        for query in queries
    ]
    
    # Execute all queries in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Map queries to results
    query_results = {}
    for query, result in zip(queries, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to retrieve papers for query '{query}': {result}")
            query_results[query] = []
        else:
            query_results[query] = result
            logger.info(f"Query '{query}': {len(result)} papers retrieved")
    
    total_papers = sum(len(papers) for papers in query_results.values())
    logger.info(f"Batch retrieval complete: {total_papers} total papers across {len(queries)} queries")
    
    return query_results
