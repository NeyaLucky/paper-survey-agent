import asyncio
import logging

from paper_survey_agent.llm.client import llm_client
from paper_survey_agent.llm.prompts import SURVEY_SYNTHESIS_SYSTEM_PROMPT
from paper_survey_agent.models.paper import SummarizedPaper


logger = logging.getLogger(__name__)


def format_papers_for_synthesis(papers: list[SummarizedPaper]) -> str:
    context_parts = []

    for p in papers:
        author_last = p.authors[0].split()[-1] if p.authors else "Unknown"
        year = p.published_date.year if p.published_date else "n.d."
        citation_key = f"{author_last} et al., {year}"

        entry = (
            f"--- Paper Reference: [{citation_key}] ---\n"
            f"Title: {p.title}\n"
            f"Authors: {', '.join(p.authors)}\n"
            f"Date: {p.published_date}\n"
            f"Summary: {p.summary}\n"
            f"Key Findings:\n" + "\n".join([f"- {kf}" for kf in p.key_findings]) + "\n"
        )
        context_parts.append(entry)

    return "\n".join(context_parts)


async def synthesize_survey(topic: str, papers: list[SummarizedPaper]) -> str:
    if not papers:
        return "No papers provided to synthesize."

    logger.info(f"🧪 Synthesizing survey for topic '{topic}' from {len(papers)} papers...")

    papers_context = format_papers_for_synthesis(papers)

    user_prompt = (
        f"Topic: {topic}\n\n"
        f"Here are the summaries of the relevant papers:\n\n"
        f"{papers_context}\n\n"
        f"Please write the State of the Art survey now."
    )

    try:
        response = await asyncio.to_thread(
            llm_client.generate, prompt=user_prompt, system_prompt=SURVEY_SYNTHESIS_SYSTEM_PROMPT
        )

        logger.info("✅ Survey synthesis complete.")
        return response

    except Exception as e:
        logger.error(f"Failed to synthesize survey: {e}")
        return f"Error generating survey: {e}"
