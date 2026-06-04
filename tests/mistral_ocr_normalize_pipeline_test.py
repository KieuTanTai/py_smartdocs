from pathlib import Path
from backend.apps.llm.llm_ocr.mistral_uploader import MistralUploader
from backend.apps.services.rag_base.storage.storage_service import FileStorageService
from backend.apps.llm.llm_ocr.llm_ocr_factory import LLMOCRFactory
from backend.apps.services.rag_base.extract.extract_content_service import ExtractContentService
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.enums.e_provider_name import EProviderName
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.core.chunk.chunker import Chunker

logger = DEFAULT_LOGGER
factory = LLMOCRFactory(DEFAULT_CONFIG_PROVIDER, logger)
uploader = MistralUploader(logger)

def run_pipeline(pdf_path: str) -> None:
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    storage_dir = output_dir / "storage"
    storage = FileStorageService(storage_dir, uploader, logger)
    extract_content = ExtractContentService(factory, storage, logger)
    
    # 1. OCR Extraction
    response = extract_content.extract_from_file_text(Path(pdf_path), EProviderName.MISTRAL)
    extracted_text = response.content if hasattr(response, "content") else response
    file_id = "test_pipeline_file"

    # 2. Normalize
    normalizer = Normalize(logger)
    normalized_text = normalizer.normalize(extracted_text)

    # 3. Chunking
    chunker = Chunker(logger, chunk_size=1000, overlap=200)
    chunks = chunker.create_chunks(normalized_text)

    output_path = output_dir / f"normalized_{file_id}.md"
    output_path.write_text(normalized_text, encoding="utf-8")
    print(f"Normalized output written to: {output_path}")

    chunks_path = output_dir / f"chunks_{file_id}.md"
    with open(chunks_path, "w", encoding="utf-8") as file:
        for i, chunk in enumerate(chunks):
            file.write(f"--- Chunk {i + 1} ---\n")
            file.write("\n" + chunk + "\n\n")
    print(f"Chunked output written to: {chunks_path}")


if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parents[2]
    pdf_path = (
        root_dir / "docs" / "pdfs_test" / "Báo cáo tài chính Kiểm toán năm 2025.pdf"
    )
    run_pipeline(str(pdf_path))

