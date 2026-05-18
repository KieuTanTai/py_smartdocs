from pathlib import Path

from backend.apps.interfaces.base_rag.extract.i_ocr_response import IOCRResponse
from backend.apps.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR
from sys_services.enums.e_provider_name import EProviderName
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER
from backend.apps.utils.is_content_empty import check_empty_content
from backend.apps.interfaces.base_rag.extract.i_extract_content import IExtractContent

class MistralOCRExtractor(ILLMOCR):
    provider_name = EProviderName.MISTRAL.value

    def __init__(self, api_key: str, model: str, timeout: float = 60.0, logger: ILogger | None = None):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.logger = logger or DEFAULT_LOGGER

    async def extract_text_from_image(self, image_path: Path) -> str:
        """
        Extract text from image using OCR.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as a string
        """
        pass

    async def extract_text_from_document(self, document_path: Path) -> str:
        """
        Extract text from document using OCR.

        Args:
            document_path: Path to the document file

        Returns:
            Extracted text as a string
        """
        pass
