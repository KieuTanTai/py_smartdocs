from datetime import datetime
from pathlib import Path

from backend.apps.core.interfaces.system.i_logging import ILogger

def create_destination_dir_by_time(metadata_dir: Path) -> Path:
    """Create a destination directory based on the current date in the format 'YYYY-MM-DD' under the given metadata directory. It will create the directory if it does not exist and return the path to the destination directory."""

    destination_dir = metadata_dir / f"{datetime.now().strftime('%Y-%m-%d')}"
    destination_dir.mkdir(parents=True, exist_ok=True)
    return destination_dir

def create_path_file(metadata_dir: Path, name: str, file_type: str, logger: ILogger | None = None) -> Path:
    """Create a file path for the given name and file type under a destination directory based on the current date in the metadata directory. It will return the path to the file, but will not create the file itself."""
    destination_dir = create_destination_dir_by_time(metadata_dir)
    destination_file = destination_dir / f"{name}.{file_type}"
    if logger is not None:
        logger.info(f"Created file path for '{name}' with type '{file_type}' at '{destination_file}'", Path(__file__).name, method_call=create_path_file.__name__)
    return destination_file

def is_existed_in_metadata(metadata_dir: Path, name: str, file_type: str, logger: ILogger | None = None) -> Path | None:
    """Check if a metadata file with the given name and type exists in the metadata directory. It will log the existence check and return the path if the file exists, or None if it does not."""

    metadata_path = metadata_dir / f"{datetime.now().strftime('%Y-%m-%d')}" / f"{name}.{file_type}"
    is_existed = metadata_path if metadata_path.exists() else None
    if logger is not None:
        if is_existed:
            logger.info(f"Metadata for '{name}' already exists at '{metadata_path}'", Path(__file__).name, method_call=is_existed_in_metadata.__name__)
        else:
            logger.info(f"Metadata for '{name}' does not exist in '{metadata_dir}'", Path(__file__).name, method_call=is_existed_in_metadata.__name__)
    return is_existed

def delete_file_metadata_with_file_path(file_path: Path, logger: ILogger | None = None) -> int:
    """Delete the metadata file at the given file path. It will log the deletion process and return 1 if the file was deleted, or 0 if the file did not exist."""

    if file_path.exists():
        file_path.unlink()
        if logger is not None:
            logger.info(f"Deleted metadata file at '{file_path}'", Path(__file__).name, method_call=delete_file_metadata_with_file_path.__name__)
        return 1
    else:
        if logger is not None:
            logger.warning(f"Metadata file at '{file_path}' does not exist and cannot be deleted", Path(__file__).name, method_call=delete_file_metadata_with_file_path.__name__)
        return 0

def clear_all_files_on_path(metadata_dir: Path, logger: ILogger | None = None) -> int:
    """
    Clear all files in the given metadata directory. It will log the deletion process and return the count of deleted files.
    """
    deleted_count = 0
    if metadata_dir.exists():
        for file in metadata_dir.glob("**/*"):
            if file.is_file():
                file.unlink()
                deleted_count += 1
                if logger is not None:
                    logger.info(f"Deleted metadata file at '{file}'", Path(__file__).name, method_call=clear_all_files_on_path.__name__)
    else:
        if logger is not None:
            logger.warning(f"Metadata directory '{metadata_dir}' does not exist and cannot be cleared", Path(__file__).name, method_call=clear_all_files_on_path.__name__)
    return deleted_count

def delete_file_metadata_with_file_name(metadata_dir: Path, name: str, file_type: str, logger: ILogger | None = None) -> int:
    """Delete the metadata file with the given name and type in the metadata directory. It will log the deletion process and return 1 if the file was deleted, or 0 if the file did not exist."""

    file_path = metadata_dir.glob(f"**/{name}.{file_type}")
    file_path = next(file_path, None)
    if file_path is None:
        if logger is not None:
            logger.warning(f"Metadata file for '{name}' with type '{file_type}' does not exist in '{metadata_dir}' and cannot be deleted", Path(__file__).name, method_call=delete_file_metadata_with_file_name.__name__)
        return 0
    return delete_file_metadata_with_file_path(file_path, logger)