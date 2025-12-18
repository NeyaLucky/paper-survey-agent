import asyncio

from loguru import logger

from paper_survey_agent.models.paper import SummarizedPaper
from paper_survey_agent.tools import (
    generate_search_query,
    search_and_load_papers_txt,
    summarize_papers,
    synthesize_survey,
)


class PaperSurveyAgent:
    async def run(self, topic: str) -> tuple[list[SummarizedPaper], str] | None:
        logger.info(f" Agent started for topic: '{topic}'")

        logger.info(" Step 1: Refining search query...")
        refined_query = await asyncio.to_thread(generate_search_query, topic)
        if refined_query != topic:
            logger.info(f"   Refined query: '{refined_query}'")

        logger.info(f" Step 2: Searching and downloading papers for '{refined_query}'...")
        processed_papers = await search_and_load_papers_txt(refined_query)

        if not processed_papers:
            logger.warning(" No papers found or downloaded. Aborting survey.")
            return None

        logger.info(f"   Successfully loaded text for {len(processed_papers)} papers.")

        logger.info(" Step 3: Reading and summarizing papers...")
        summarized_papers = await summarize_papers(processed_papers)

        if not summarized_papers:
            logger.warning(" Failed to generate summaries. Aborting.")
            return None

        logger.info(f"   Generated summaries for {len(summarized_papers)} papers.")

        logger.info(" Step 4: Synthesizing final literature review...")
        survey_report = await synthesize_survey(topic, summarized_papers)

        logger.info(" Agent finished successfully.")
        return summarized_papers, survey_report
