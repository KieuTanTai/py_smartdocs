from pathlib import Path
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.logging import DEFAULT_LOGGER
from mistralai.client import Mistral

ROOT_DIR = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT_DIR / "docs" / "pdfs_test" / "Báo cáo tài chính Kiểm toán năm 2025.pdf"

client = Mistral(api_key=MISTRAL_CONFIG["api_key"])
logger = DEFAULT_LOGGER
uploaded_pdf = client.files.upload(
    file={
        "file_name": "SmartDocsAI.pdf",
        "content": open(
            PDF_PATH,
            "rb",
        ),
    },
    purpose="ocr",
)

print("Uploaded PDF response:", uploaded_pdf)
print("Uploaded PDF ID:", uploaded_pdf.id)
retrieved_file = client.files.retrieve(file_id=uploaded_pdf.id)  # type: ignore
print("Retrieved file response:", retrieved_file)
signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)  # type: ignore
print("Signed URL response:", signed_url)

ocr_response = client.ocr.process(
    model=MISTRAL_CONFIG["ocr_model"],
    document={
        "type": "document_url",
        "document_url": signed_url.url,
    },
    table_format="html",  # default is None
    # extract_header=True, # default is False
    # extract_footer=True, # default is False
    include_image_base64=True,
)
try:
    with open(Path(__file__).parent / "output" / f"output_{uploaded_pdf.id}.md", "w") as f:  # type: ignore
        for page in ocr_response.pages:
            f.write(page.markdown)
    logger.info(
        f"OCR output successfully written to file: output_{uploaded_pdf.id}.md",
        source=Path(__file__).name,
    )
except Exception as e:
    logger.error(
        f"An error occurred while writing OCR output to file: {e}",
        source=Path(__file__).name,
    )

# client.files.delete(file_id=uploaded_pdf.id)  # type: ignore
