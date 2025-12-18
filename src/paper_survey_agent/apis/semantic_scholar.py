import asyncio
from datetime import datetime
from typing import Optional

import httpx
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from paper_survey_agent.apis.base import BaseScientificAPI
from paper_survey_agent.models.paper import Paper
from paper_survey_agent.settings import settings


class SemanticScholarAPI(BaseScientificAPI):
    BASE_URL = settings.SEMANTIC_SCHOLAR_API_BASE_URL

    RATE_LIMIT_DELAY = 1.0

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

    def __init__(self, api_key: str | None = None, timeout: int = settings.SEMANTIC_SCHOLAR_TIMEOUT):
        self.api_key = api_key
        self.timeout = timeout
        self.last_request_time = 0.0

        headers = {"Accept": "application/json"}
        if api_key:
            headers["x-api-key"] = api_key

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=timeout,
        )

        logger.info(f"Initialized SemanticScholarAPI (authenticated: {bool(api_key)}, timeout: {timeout}s)")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _rate_limit(self):
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
            if e.response.status_code == 429:
                logger.warning("Rate limit hit (429), waiting before retry...")
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
                raise ValueError(f"Paper not found on Semantic Scholar: {paper_id}") from e
            logger.error(f"Semantic Scholar API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve Semantic Scholar paper {paper_id}: {e}", exc_info=True)
            raise

    def _convert_to_paper(self, data: dict) -> Paper:
        paper_id = data.get("paperId", "")
        title = data.get("title", "Unknown Title")
        authors_data = data.get("authors", [])
        authors = [author.get("name", "Unknown") for author in authors_data]
        abstract = data.get("abstract") or "No abstract available"

        pub_date_str = data.get("publicationDate") or data.get("year")
        if pub_date_str:
            try:
                if isinstance(pub_date_str, int):
                    published_date = datetime(pub_date_str, 1, 1).date()
                else:
                    published_date = datetime.fromisoformat(pub_date_str).date()
            except (ValueError, TypeError):
                published_date = datetime.now().date()
        else:
            published_date = datetime.now().date()

        url = data.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}"

        pdf_data = data.get("openAccessPdf")
        pdf_url = pdf_data.get("url") if pdf_data else None

        citations_count = data.get("citationCount")

        categories = data.get("fieldsOfStudy") or []

        external_ids = data.get("externalIds") or {}
        arxiv_id = external_ids.get("ArXiv")
        if arxiv_id:
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
        await self.client.aclose()
        logger.info("Closed SemanticScholarAPI client")
