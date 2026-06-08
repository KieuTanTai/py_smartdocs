import os
from pathlib import Path

from backend.apps.core.interfaces.system.i_logging import ILogger


def check_file_path(file_path: Path, logger: ILogger):
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist.", source=Path(__file__).name)
        raise FileNotFoundError(f"File {file_path} does not exist.")
    if not file_path.is_file():
        logger.error(f"Path {file_path} is not a file.", source=Path(__file__).name)
        raise ValueError(f"Path {file_path} is not a file.")


def check_storage_dir_exists_and_accessible(
    storage_dir: Path, logger: ILogger
):
    if not os.path.exists(storage_dir):
        logger.warning(
            f"Storage directory does not exist: {storage_dir} and will be created.",
            source=Path(__file__).name,
        )
        os.makedirs(storage_dir, exist_ok=True)

    if not os.access(storage_dir, os.W_OK | os.R_OK):
        logger.error(
            f"Storage directory is not accessible: {storage_dir}",
            source=Path(__file__).name,
        )
        raise PermissionError(f"Storage directory is not accessible: {storage_dir}")
