import asyncio
import logging
from pathlib import Path

import aiofiles
import pymupdf

from paper_survey_agent.settings import settings


logger = logging.getLogger(__name__)


def extract_text_from_pdf_sync(pdf_path: Path) -> str:
    try:
        with pymupdf.open(pdf_path) as doc:
            full_text = []
            for page in doc:
                text = page.get_text()
                full_text.append(text)

        return "\n\n".join(full_text)
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return ""


async def convert_single_pdf(paper_id: str, pdf_path: Path, txt_dir: Path) -> tuple[str, Path | None]:
    txt_filename = f"{pdf_path.stem}.txt"
    txt_path = txt_dir / txt_filename

    if txt_path.exists():
        logger.debug(f"Text file already exists: {txt_path}")
        return paper_id, txt_path

    loop = asyncio.get_running_loop()

    try:
        text_content = await loop.run_in_executor(None, extract_text_from_pdf_sync, pdf_path)

        if not text_content:
            logger.warning(f"No text extracted for {paper_id}")
            return paper_id, None

        async with aiofiles.open(txt_path, "w", encoding="utf-8") as f:
            await f.write(text_content)

        logger.info(f"Converted PDF to text: {txt_filename}")
        return paper_id, txt_path

    except Exception as e:
        logger.error(f"Failed to convert {paper_id}: {e}")
        return paper_id, None


async def convert_pdfs_to_text(pdf_paths: dict[str, Path], destination_dir: Path | None = None) -> dict[str, Path]:
    if destination_dir is None:
        destination_dir = Path(settings.DATA_DIR) / "txts"

    destination_dir.mkdir(parents=True, exist_ok=True)

    tasks = [convert_single_pdf(pid, path, destination_dir) for pid, path in pdf_paths.items()]

    results = await asyncio.gather(*tasks)

    return {pid: path for pid, path in results if path is not None}
