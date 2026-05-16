from pathlib import Path
from backend.apps.core.extract_file.mistral_ocr import MistralOCRExtractor
from backend.apps.services.base_pipeline.normalize_service import Normalize
from backend.apps.services.base_pipeline.chunking_service import Chunking


def run_pipeline(pdf_path: str) -> None:
    extracted_text, file_id = (
        MistralOCRExtractor.extract_text_from_pdf_with_mistral_ocr(pdf_path)
    )
    normalized_text, file_id = Normalize.normalize_markdown_file(
        extracted_text, file_id
    )

    chunks = Chunking.chunk_text_by_token(
        normalized_text,
        chunk_size=1000,
        chunk_overlap=200,
    )

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"normalized_{file_id}.md"
    output_path.write_text(normalized_text)
    print(f"Normalized output written to: {output_path}")

    chunks_path = output_dir / f"chunks_{file_id}.md"
    with open(chunks_path, "w") as file:
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
