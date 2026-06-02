import io
from pathlib import Path
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.logging import DEFAULT_LOGGER
from mistralai.client import Mistral
from mistralai.client.models import CreateFileResponse

ROOT_DIR = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT_DIR / "docs" / "pdfs_test" / "Báo cáo tài chính Kiểm toán năm 2025.pdf"

client = Mistral(api_key=MISTRAL_CONFIG["api_key"])
logger = DEFAULT_LOGGER


def test_fake_text_upload() -> CreateFileResponse:
    """Case: user uploads a text file that is not on the server machine."""
    fake_text = "User uploaded content from a remote device."
    fake_file = io.BytesIO(fake_text.encode("utf-8"))
    try:
        fake_upload = client.files.upload(
            file={
                "file_name": "remote_note.txt",
                "content": fake_file,
            },
            purpose="ocr",
        )
        print("Uploaded fake text file:", fake_upload)
        logger.info(
            "Fake text file uploaded successfully for remote user test.",
            source=Path(__file__).name,
        )
        return fake_upload
    except Exception as e:
        logger.error(
            f"Failed to upload fake text file: {e}",
            source=Path(__file__).name,
        )
        print(f"Failed to upload fake text file: {e}")
        # create a dummy file with this content on server with touch (on linux) locate in folder output and using this path call test_local_pdf_ocr to test the OCR process with this dummy file
        dummy_file_path = Path(__file__).parent / "output" / "dummy_remote_note.txt"
        dummy_file_path.parent.mkdir(parents=True, exist_ok=True)
        dummy_file_path.touch(exist_ok=True)
        dummy_file_path.write_text(fake_text)
        logger.info(
            f"Created dummy file at {dummy_file_path} for testing OCR with remote user content.",
            source=Path(__file__).name,
        )
        return client.files.upload(
            file={
                "file_name": "dummy_remote_note.txt",
                "content": open(dummy_file_path, "rb"),
            },
            purpose="ocr",
        )


def process_ocr(uploaded_pdf: CreateFileResponse) -> None:
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
        confidence_scores_granularity="page",
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


def test_local_pdf_ocr() -> CreateFileResponse:
    """Case: user uploads a PDF file that is on the server machine."""
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
    process_ocr(uploaded_pdf)
    return uploaded_pdf


if __name__ == "__main__":
    fake_upload = test_fake_text_upload()
    real_upload = test_local_pdf_ocr()
    process_ocr(real_upload)
    process_ocr(fake_upload)
