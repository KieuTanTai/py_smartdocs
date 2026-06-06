import asyncio
import shutil
from pathlib import Path

from backend.apps.llm.llm_ocr.mistral_uploader import MistralUploader
from backend.apps.services.rag_base.storage.storage_service import FileStorageService
from backend.apps.llm.llm_ocr.llm_ocr_factory import LLMOCRFactory
from backend.apps.services.rag_base.extract.extract_content_service import (
    ExtractContentService,
)
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from backend.apps.core.enums.e_provider_name import EProviderName

class Extractor:
    """Wrapper class to match the test's expected extract API."""
    def __init__(self, extract_content_service, logger=None):
        self.extract_content_service = extract_content_service
        self.logger = logger

    async def extract(self, file_path: Path):
        # Always use Mistral provider for this test
        provider = EProviderName.MISTRAL
        suffix = file_path.suffix.lower()
        if suffix in [".png", ".jpg", ".jpeg", ".webp"]:
            return self.extract_content_service.extract_from_file_image(file_path, provider)
        else:
            return self.extract_content_service.extract_from_file_text(file_path, provider)


ROOT_DIR = Path(__file__).resolve().parents[2]
PDF_SOURCE = (
    ROOT_DIR / "docs" / "pdfs_test" / "Báo cáo tài chính Kiểm toán năm 2025.pdf"
)
IMAGE_SOURCE = (
    ROOT_DIR / "docs" / "pdfs_test" / "1000125758-Picsart-AiImageEnhancer.jpg"
)

logger = DEFAULT_LOGGER


def _prepare_input_file(source_path: Path, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    destination_path = work_dir / source_path.name
    shutil.copy2(source_path, destination_path)
    return destination_path


async def run_text_ocr(output_dir: Path) -> None:
    input_dir = output_dir / "input"
    file_path = _prepare_input_file(PDF_SOURCE, input_dir)

    factory = LLMOCRFactory(DEFAULT_CONFIG_PROVIDER, logger)
    uploader = MistralUploader(logger)
    storage_dir = output_dir / "storage"
    storage = FileStorageService(storage_dir, uploader, logger)
    extract_content = ExtractContentService(
        factory, storage, logger
    )
    ocr = Extractor(extract_content, logger)

    response = await ocr.extract(file_path)
    output_path = output_dir / f"mistral_ocr_text_{file_path.stem}.md"
    output_path.write_text(response.content)
    logger.info(
        f"Mistral OCR text output written to: '{output_path}'",
        source=Path(__file__).name,
    )


async def run_image_ocr(output_dir: Path) -> None:
    input_dir = output_dir / "input"
    file_path = _prepare_input_file(IMAGE_SOURCE, input_dir)

    factory = LLMOCRFactory(DEFAULT_CONFIG_PROVIDER, logger)
    uploader = MistralUploader(logger)
    storage_dir = output_dir / "storage"
    storage = FileStorageService(storage_dir, uploader, logger)
    extract_content = ExtractContentService(
        factory, storage, logger
    )
    ocr = Extractor(extract_content, logger)

    response = await ocr.extract(file_path)
    output_path = output_dir / f"mistral_ocr_image_{file_path.stem}.md"
    output_path.write_text(response.content)
    logger.info(
        f"Mistral OCR image output written to: '{output_path}'",
        source=Path(__file__).name,
    )


if __name__ == "__main__":
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    asyncio.run(run_text_ocr(output_dir))
    asyncio.run(run_image_ocr(output_dir))
