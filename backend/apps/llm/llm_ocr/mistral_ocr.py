from pathlib import Path
from typing import Dict, Any
from mistralai import Mistral
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.utils.is_content_empty import check_empty_content
from backend.apps.core.interfaces.dataclass.ocr.i_ocr_response import IOCRResponse, OCRPage, OCRUsageInfo

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
        try:
            self.client = Mistral(api_key=self.api_key)
            self.logger.info(
                f"Successfully initialized Mistral client",
                source=str(self.__class__), call_by="__init__", method_call="__init__"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to initialize Mistral client: {e}",
                source=str(self.__class__), call_by="__init__", method_call="__init__"
            )
            raise ValueError(f"Failed to initialize Mistral client. Please check your internet connection: {e}")

    # region - Public Methods
    def process_ocr(
        self, uploaded_pdf: ICreateFileResponse, call_by: str = ""
    ) -> IOCRResponse:
        # Implementation for processing OCR on the uploaded PDF
        self.logger.info(
            f"Starting OCR process for file ID: {uploaded_pdf.id}",
            source=str(self.__class__),
            call_by=call_by,
            method_call=self.process_ocr.__name__,
        )
        try:
            signed_url = self.client.files.get_signed_url(file_id=uploaded_pdf.id)
            mime_type = self.__get_mime_type(uploaded_pdf, call_by=call_by)
            document = self.__get_document_object_by_mime_type(
                mime_type, signed_url.url
            )  # This will raise ValueError if MIME type is unsupported, otherwise it will return the appropriate document object for Mistral OCR processing
            return self.__execute_ocr(document, uploaded_pdf, call_by=call_by)  # This will raise exceptions if OCR processing fails
        except ValueError as ve:
            self.logger.error(
                f"Value error during OCR processing for file ID: {uploaded_pdf.id} - {ve}",
                source=str(self.__class__),call_by=call_by, method_call=self.process_ocr.__name__
            )
            raise ve
        except Exception as e:
            self.logger.error(
                f"Error during OCR processing for file ID: {uploaded_pdf.id} - {e}",
                source=str(self.__class__), call_by=str(self.__class__), method_call=self.process_ocr.__name__
            )
            raise e

    def __execute_ocr(self, document: Dict[str, Any], uploaded_pdf: ICreateFileResponse, call_by: str = "") -> IOCRResponse:
        try:
            # Call Mistral OCR API with timeout from configuration
            native_ocr_response = self.client.ocr.process(
                model=self.model,
                document=document,
                timeout_ms=int(self.timeout_seconds * 1000),
                include_image_base64=True,
                confidence_scores_granularity="page",
            )

            # Convert native response to our custom IOCRResponse
            ocr_response = self.__convert_to_iocr_response(native_ocr_response)

            self.logger.info(
                f"OCR process completed successfully for file ID: {uploaded_pdf.id}",
                source=str(self.__class__), call_by=call_by, method_call=self.process_ocr.__name__
            )
            return ocr_response
        except TimeoutError as te:
            self.logger.error(
                f"Timeout error during OCR processing (timeout: {self.timeout_seconds}s) - {te}",
                source=str(self.__class__), call_by=call_by, method_call=self.__execute_ocr.__name__
            )
            raise ValueError(f"OCR processing timed out after {self.timeout_seconds} seconds. Please try with a smaller file or increase timeout.")
        except Exception as e:
            self.logger.error(
                f"Error during OCR processing - {e}",
                source=str(self.__class__), call_by=call_by, method_call=self.__execute_ocr.__name__
            )
            raise e

    def __convert_to_iocr_response(self, native_response: Any) -> IOCRResponse:
        """Convert native Mistral OCR response to our custom IOCRResponse dataclass."""
        # Extract pages
        pages = []
        if hasattr(native_response, 'pages'):
            for page in native_response.pages:
                markdown = getattr(page, 'markdown', '')
                page_number = getattr(page, 'page_number', None)
                pages.append(OCRPage(markdown=markdown, page_number=page_number))
        
        # Extract usage info
        usage_info = OCRUsageInfo(pages_processed=0, doc_size_bytes=None)
        if hasattr(native_response, 'usage_info'):
            usage_info = OCRUsageInfo(
                pages_processed=getattr(native_response.usage_info, 'pages_processed', 0),
                doc_size_bytes=getattr(native_response.usage_info, 'doc_size_bytes', None)
            )
        
        # Build IOCRResponse
        return IOCRResponse(
            model=getattr(native_response, 'model', self.model),
            pages=pages,
            usage_info=usage_info,
            id=getattr(native_response, 'id', None),
            created_at=getattr(native_response, 'created_at', None)
        )


    def __get_mime_type(self, file_response: ICreateFileResponse, call_by: str = "") -> str:
        if hasattr(file_response, "mimetype") and file_response.mimetype:
            return str(file_response.mimetype)
        else:
            self.logger.warning(
                f"File response does not have 'mimetype' attribute or mimetype is None. Defaulting to 'application/pdf'.",
                source=str(self.__class__), call_by=call_by, method_call=self.__get_mime_type.__name__
            )
            return "application/pdf"

    def __get_document_object_by_mime_type(
        self, mime_type: str, signed_url: str
    ) -> Dict[str, Any]:
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
