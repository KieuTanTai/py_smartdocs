"""
Mime type helpers.
"""

from pathlib import Path

from backend.apps.core.enums.e_mime_type import EMimeType
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER


def get_mime_type_from_path(file_path: Path) -> EMimeType:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return EMimeType.PDF
    if suffix == ".docx":
        return EMimeType.DOCX
    if suffix == ".txt":
        return EMimeType.TXT
    if suffix == ".jpeg":
        return EMimeType.JPEG
    if suffix == ".png":
        return EMimeType.PNG
    if suffix == ".jpg":
        return EMimeType.JPG
    if suffix in {".tif", ".tiff"}:
        return EMimeType.TIFF
    raise ValueError(f"Unsupported file extension: {suffix}")


def get_dir_by_mime_type(
    storage_dir: Path, mime_type: EMimeType, logger: ILogger | None = None
) -> Path:
    logger = logger or DEFAULT_LOGGER
    if mime_type == EMimeType.PDF:
        return storage_dir / "pdf"
    if mime_type == EMimeType.DOCX:
        return storage_dir / "docx"
    if mime_type == EMimeType.TXT:
        return storage_dir / "txt"
    if mime_type == EMimeType.JPEG:
        return storage_dir / "images" / "jpeg"
    if mime_type == EMimeType.PNG:
        return storage_dir / "images" / "png"
    if mime_type == EMimeType.JPG:
        return storage_dir / "images" / "jpg"
    if mime_type == EMimeType.TIFF:
        return storage_dir / "images" / "tiff"
    logger.error(
        f"Unsupported MIME type: {mime_type}",
        source=Path(__file__).name,
    )
    raise ValueError(f"Unsupported MIME type: {mime_type}")
