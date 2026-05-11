import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve()
ROOT_DIR = CURRENT_DIR.parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.logging import Logger
from sys_services.enums.type_message import TypeMessage
from mistralai.client import Mistral

def extract_text_from_pdf_with_mistral_ocr(pdf_path: str) -> str:
    source_log = Path(__file__).name
    try:
        client = Mistral(api_key=MISTRAL_CONFIG["apiKey"])
        uploaded_pdf = client.files.upload(
            file={
                "file_name": os.path.basename(pdf_path),
                "content": open(pdf_path, "rb"),
            },
            purpose="ocr",
        )

        signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)  # type: ignore

        ocr_response = client.ocr.process(
            model=MISTRAL_CONFIG["model"],
            document={
                "type": "document_url",
                "document_url": signed_url.url,
            },
            table_format="html",  # default is None
            extract_header=True, # default is False
            extract_footer=True, # default is False
            include_image_base64=True,
        )

        extracted_text = "\n".join(page.markdown for page in ocr_response.pages)
        if(extracted_text.strip() == ""):
            Logger.log(
                TypeMessage.WARNING,
                "Extracted text is empty. This may indicate an issue with the OCR process.",
                source_log=source_log
            )
        client.files.delete(file_id=uploaded_pdf.id)  # type: ignore
        return extracted_text
    except Exception as e:
        Logger.log(
            TypeMessage.ERROR,
            f"An error occurred during OCR extraction: {e}",
            source_log=source_log
        )
        return ""