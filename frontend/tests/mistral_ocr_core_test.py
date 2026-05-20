import asyncio
import shutil
from pathlib import Path

from backend.apps.core.extract_file.mistral_ocr import MistralOCR
from backend.apps.llm.llm_ocr.mistral_uploader import MistralUploader
from backend.apps.core.storage.storage import FileStorage
from backend.apps.llm.llm_ocr.llm_ocr_factory import LLMOCRFactory
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER

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
    storage = FileStorage(storage_dir, factory, uploader, logger)
    ocr = MistralOCR(factory, storage, logger)

    response = await ocr.extract_from_file_text(file_path)
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
    storage = FileStorage(storage_dir, factory, uploader, logger)
    ocr = MistralOCR(factory, storage, logger)

    response = await ocr.extract_from_file_image(file_path)
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
