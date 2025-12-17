import logging
from pathlib import Path
import shutil

from paper_survey_agent.settings import settings


logger = logging.getLogger(__name__)


def clear_data_directory() -> None:
    data_dir = Path(settings.DATA_DIR)

    if not data_dir.exists():
        logger.info(f"Data directory {data_dir} does not exist. Creating it.")
        data_dir.mkdir(parents=True, exist_ok=True)
        return

    logger.warning(f"Clearing all data from: {data_dir}")

    try:
        shutil.rmtree(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Data directory cleared and recreated successfully.")

    except PermissionError:
        logger.error(f"Permission denied: Could not delete {data_dir}. Close any open files.")
        raise
    except Exception as e:
        logger.error(f"Failed to clear data directory: {e}")
        raise
