from pathlib import Path
from mistralai.client import Mistral, models
from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.utils.is_content_empty import check_empty_content


class MistralLLMOCR(ILLMOCR):
    provider_name = EProviderName.MISTRAL.value

    def __init__(
        self,
        api_key: str,
        model: str,
        provider_name: str,
        timeout_seconds: float,
        logger: ILogger,
    ):
        if not api_key:
            raise ValueError("API key is required for Mistral OCR Extractor.")
        self.api_key = api_key
        self.model = model
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.logger = logger
        self.client = Mistral(api_key=self.api_key)

    # region - Public Methods
    def process_ocr(
        self, uploaded_pdf: ICreateFileResponse
    ) -> str:
        # Implementation for processing OCR on the uploaded PDF
        self.logger.info(
            f"Starting OCR process for file ID: {uploaded_pdf.id}",
            source=str(self.__class__),
        )
        try:
            source_log = f"{Path(__file__).parent.absolute()}/{Path(__file__).name}"
            signed_url = self.client.files.get_signed_url(file_id=uploaded_pdf.id)
            mime_type = self.__get_mime_type(uploaded_pdf)
            document = self.__get_document_object_by_mime_type(
                mime_type, signed_url.url
            )  # This will raise ValueError if MIME type is unsupported, otherwise it will return the appropriate document object for Mistral OCR processing

            ocr_response = self.client.ocr.process(
                model=self.model,
                document=document,
                timeout_ms=int(self.timeout_seconds * 1000),
                table_format="html",  # default is None
                include_image_base64=True,
                confidence_scores_granularity="page",
            )

            extracted_text = "\n".join([page.markdown for page in ocr_response.pages])
            if self.__validate_response_text(extracted_text, source_log) is False:
                raise ValueError("Extracted text is empty or contains only whitespace.")
            return extracted_text
            
        except ValueError as ve:
            self.logger.error(
                f"Value error during OCR processing for file ID: {uploaded_pdf.id} - {ve}",
                source=str(self.__class__),
            )
            raise ve
        except Exception as e:
            self.logger.error(
                f"Error during OCR processing for file ID: {uploaded_pdf.id} - {e}",
                source=str(self.__class__),
            )
            raise e


    def __validate_response_text(self, text: str, source_log: str) -> bool:
        if check_empty_content(text, source_log, self.logger) is False:
            self.logger.warning(
                f"Extracted text is empty or contains only whitespace. Source log: {source_log}",
                source=str(self.__class__),
            )
            return False
        return True

    def __get_mime_type(self, file_response: ICreateFileResponse) -> str:
        if hasattr(file_response, "mimetype"):
            return str(file_response.mimetype)
        else:
            self.logger.warning(
                f"File response does not have 'mimetype' attribute. Defaulting to 'application/pdf'.",
                source=str(self.__class__),
            )
            return "application/pdf"

    def __get_document_object_by_mime_type(
        self, mime_type: str, signed_url: str
    ) -> models.DocumentUnion | models.DocumentUnionTypeDict:
        if mime_type in [
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            return {"type": "document_url", "document_url": signed_url}
        elif mime_type in ["image/jpeg", "image/png", "image/tiff", "image/jpg"]:
            return {"type": "image_url", "image_url": signed_url}
        else:
            raise ValueError(f"Unsupported MIME type: {mime_type}")
