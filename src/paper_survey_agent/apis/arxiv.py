from datetime import datetime
from typing import Optional

import arxiv
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from paper_survey_agent.apis.base import BaseScientificAPI
from paper_survey_agent.models.paper import Paper
from paper_survey_agent.settings import settings


class ArxivAPI(BaseScientificAPI):
    def __init__(self, page_size: int = settings.ARXIV_PAGE_SIZE, delay_seconds: int = settings.ARXIV_DELAY_SECONDS):
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
        max_results: int = settings.MAX_RESULTS_PER_SOURCE,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
    ) -> list[Paper]:
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
        arxiv_id = result.entry_id.split("/")[-1].split("v")[0]
        published_date = result.published.date()

        authors = [author.name for author in result.authors]
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
            citations_count=None,
            categories=categories,
        )
