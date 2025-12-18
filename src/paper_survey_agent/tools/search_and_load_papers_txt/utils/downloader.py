import asyncio
from pathlib import Path
import re
from typing import Optional

import httpx
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from paper_survey_agent.models.paper import Paper
from paper_survey_agent.settings import settings


async def download_papers(papers: list[Paper], destination_dir: str | Path | None = None) -> dict[str, Path]:
    if destination_dir is None:
        destination_dir = Path(settings.DATA_DIR) / "pdfs"
    else:
        destination_dir = Path(destination_dir)

    destination_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting download for {len(papers)} papers to {destination_dir}")

    semaphore = asyncio.Semaphore(settings.PDF_MAX_CONCURRENT_DOWNLOADS)

    async def _download_safe(paper: Paper) -> tuple[str, Path | None]:
        async with semaphore:
            return await _download_single_paper(paper, destination_dir)

    tasks = [_download_safe(paper) for paper in papers if paper.pdf_url]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    downloaded_map = {}
    for res in results:
        if isinstance(res, tuple) and res[1] is not None:
            paper_id, path = res
            downloaded_map[paper_id] = path

    logger.info(f"Successfully downloaded {len(downloaded_map)}/{len(papers)} PDFs")
    return downloaded_map


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=False,
)
async def _download_single_paper(paper: Paper, dest_dir: Path) -> tuple[str, Path | None]:
    if not paper.pdf_url:
        logger.warning(f"No PDF URL for paper {paper.id}")
        return paper.id, None

    safe_id = re.sub(r"[^\w\-.]", "_", paper.id)
    filename = f"{safe_id}.pdf"
    file_path = dest_dir / filename

    if file_path.exists():
        logger.debug(f"File already exists: {file_path}")
        return paper.id, file_path

    logger.debug(f"Downloading {paper.id} from {paper.pdf_url}")

    try:
        async with httpx.AsyncClient(
            timeout=settings.PDF_DOWNLOAD_TIMEOUT, follow_redirects=True, headers={"User-Agent": settings.USER_AGENT}
        ) as client:
            response = await client.get(paper.pdf_url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "application/pdf" not in content_type and "binary/octet-stream" not in content_type:
                logger.warning(f"URL {paper.pdf_url} returned {content_type}, not PDF.")
                return paper.id, None

            with open(file_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"Downloaded: {filename}")
        return paper.id, file_path

    except Exception as e:
        logger.error(f"Failed to download {paper.id}: {e}")
        if file_path.exists():
            file_path.unlink()
        raise e
