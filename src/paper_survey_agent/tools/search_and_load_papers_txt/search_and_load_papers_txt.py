import asyncio
import logging
import math

from paper_survey_agent.models.paper import ProcessedPaper
from paper_survey_agent.settings import settings
from paper_survey_agent.tools.search_and_load_papers_txt.utils.downloader import download_papers
from paper_survey_agent.tools.search_and_load_papers_txt.utils.maintenance import clear_data_directory
from paper_survey_agent.tools.search_and_load_papers_txt.utils.ranking import rank_and_deduplicate
from paper_survey_agent.tools.search_and_load_papers_txt.utils.retrieval import retrieve_papers
from paper_survey_agent.tools.search_and_load_papers_txt.utils.text_extractor import convert_pdfs_to_text


logger = logging.getLogger(__name__)


async def search_and_load_papers_txt(query: str) -> list[ProcessedPaper]:
    clear_data_directory()

    target_count = settings.MAX_PAPERS_TO_RETURN

    papers = await retrieve_papers(query=query)

    ranked_candidates = rank_and_deduplicate(papers=papers, topic=query)

    logger.info(f" Candidate pool established: {len(ranked_candidates)} papers")

    downloaded_pdfs = {}
    current_index = 0

    while len(downloaded_pdfs) < target_count and current_index < len(ranked_candidates):
        needed = target_count - len(downloaded_pdfs)

        batch_end = min(current_index + needed, len(ranked_candidates))
        batch_papers = ranked_candidates[current_index:batch_end]

        if not batch_papers:
            break

        logger.info(f"Downloading batch of {len(batch_papers)} (Need {needed} more)...")

        new_downloads = await download_papers(batch_papers)
        downloaded_pdfs.update(new_downloads)

        current_index = batch_end

    if len(downloaded_pdfs) < target_count:
        logger.warning(f"Pipeline finished with {len(downloaded_pdfs)} papers, " f"short of target {target_count}.")

    txt_paths = await convert_pdfs_to_text(downloaded_pdfs)

    results = []
    paper_map = {p.id: p for p in ranked_candidates}

    for paper_id, pdf_path in downloaded_pdfs.items():
        original_paper = paper_map.get(paper_id)
        if original_paper:
            processed_paper = ProcessedPaper(
                **original_paper.model_dump(), pdf_path=pdf_path, txt_path=txt_paths.get(paper_id)
            )
            results.append(processed_paper)

    logger.info(f" Pipeline complete. Acquired {len(results)} fully processed papers.")
    return results
