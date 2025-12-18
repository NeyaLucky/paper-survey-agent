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
    async def run(self, topic: str, progress_callback=None) -> tuple[list[SummarizedPaper], str] | None:
        def report(step, message):
            if progress_callback:
                progress_callback(step, message)
            logger.info(message)

        report(0.0, f"Agent started for topic: '{topic}'")

        report(0.05, "Step 1: Refining search query...")
        refined_query = await asyncio.to_thread(generate_search_query, topic)
        if refined_query != topic:
            report(0.12, f"Refined query: '{refined_query}'")

        report(0.2, f"Step 2: Searching and downloading papers for '{refined_query}'...")
        processed_papers = await search_and_load_papers_txt(refined_query)

        if not processed_papers:
            report(0.25, "No papers found or downloaded. Aborting survey.")
            return None

        report(0.35, f"Successfully loaded text for {len(processed_papers)} papers.")

        report(0.45, "Step 3: Reading and summarizing papers... (this may take a while)")
        summarized_papers = await summarize_papers(processed_papers)

        if not summarized_papers:
            report(0.55, "Failed to generate summaries. Aborting.")
            return None

        report(0.7, f"Generated summaries for {len(summarized_papers)} papers.")

        report(0.8, "Step 4: Synthesizing final literature review...")
        survey_report = await synthesize_survey(topic, summarized_papers)

        report(1.0, "Agent finished successfully.")
        return summarized_papers, survey_report
