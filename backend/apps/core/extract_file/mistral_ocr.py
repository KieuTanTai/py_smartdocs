import os
from pathlib import Path

from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.logging import Logger
from sys_services.enums.type_message import TypeMessage
from mistralai.client import Mistral
from backend.apps.utils.is_content_empty import check_empty_content

class MistralOCRExtractor:

    @staticmethod
    def extract_text_from_pdf_with_mistral_ocr(pdf_path: str) -> tuple[str, str]:
        source_log = f"{Path(__file__).parent.absolute()}/{Path(__file__).name}"
        try:
            client = Mistral(api_key=MISTRAL_CONFIG["api_key"])
            uploaded_pdf = client.files.upload(
                file={
                    "file_name": os.path.basename(pdf_path),
                    "content": open(pdf_path, "rb"),
                },
                purpose="ocr",
            )

            signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)  # type: ignore

            ocr_response = client.ocr.process(
                model=MISTRAL_CONFIG["ocr_model"],
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
            if(not check_empty_content(extracted_text, source_log)):
                raise ValueError("Extracted text is empty. This may indicate an issue with the OCR extraction process.")
            
            Logger.log(
                TypeMessage.INFO,
                f"Extracted text for {source_log} is not empty. Proceeding with normalization.",
                source_log=source_log
            )
            return extracted_text, uploaded_pdf.id
        except Exception as e:
            Logger.log(
                TypeMessage.ERROR,
                f"An error occurred during OCR extraction: {e}",
                source_log=source_log
            )
            raise Exception(f"OCR extraction failed: {e}")