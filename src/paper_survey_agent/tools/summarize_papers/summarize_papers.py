import asyncio
import json
import logging
from typing import Any

import aiofiles

from paper_survey_agent.llm.client import llm_client
from paper_survey_agent.llm.prompts import PAPER_SUMMARIZATION_SYSTEM_PROMPT
from paper_survey_agent.models.paper import ProcessedPaper, SummarizedPaper


logger = logging.getLogger(__name__)


def parse_llm_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parse Error: {e}. Raw Text: {cleaned[:100]}...")
        return {"summary": text, "key_findings": ["Error parsing structured findings."]}


async def summarize_single_paper(paper: ProcessedPaper, semaphore: asyncio.Semaphore) -> SummarizedPaper | None:
    if not paper.txt_path or not paper.txt_path.exists():
        logger.warning(f"Skipping {paper.id}: TXT file missing.")
        return None

    async with semaphore:
        try:
            async with aiofiles.open(paper.txt_path, encoding="utf-8") as f:
                content = await f.read()

            if len(content) > 80000:
                content = content[:80000] + "...[TRUNCATED]"

            user_prompt = f"Title: {paper.title}\n\nFull Paper Text:\n{content}"

            logger.info(f"🧠 Summarizing: {paper.title[:40]}...")

            response_text = await asyncio.to_thread(
                llm_client.generate, prompt=user_prompt, system_prompt=PAPER_SUMMARIZATION_SYSTEM_PROMPT
            )

            data = parse_llm_json(response_text)

            summary_text = data.get("summary", "No summary generated.")
            findings_list = data.get("key_findings", [])

            return SummarizedPaper(**paper.model_dump(), summary=summary_text, key_findings=findings_list)

        except Exception as e:
            logger.error(f"Failed to summarize {paper.id}: {e}")
            return None


async def summarize_papers(papers: list[ProcessedPaper]) -> list[SummarizedPaper]:
    logger.info(f"🚀 Starting summarization for {len(papers)} papers...")

    semaphore = asyncio.Semaphore(3)

    tasks = [summarize_single_paper(p, semaphore) for p in papers]
    results = await asyncio.gather(*tasks)

    valid_results = [r for r in results if r is not None]

    logger.info(f"✅ Summarized {len(valid_results)}/{len(papers)} papers successfully.")
    return valid_results
