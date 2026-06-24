"""
Extract content service interface module.
Abstract interface for file content extraction orchestration.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.ocr.i_ocr_response import IOCRResponse

from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse

class IExtractContent(ABC):
    """
    Abstract interface for content extraction.
    Orchestrates file extraction and content preparation.
    """

    @abstractmethod
    def extract(
        self,
        file_path: Path,
        provider: EProviderName,
        call_by: str = "",
    ) -> IExtractResponse:
        """
        Extract content from file.

        Args:
            file_path: Path to file
            provider: LLM provider to use for OCR extraction
            call_by: Optional string indicating the caller of this method for logging purposes
        Returns:
            IExtractResponse containing extracted text and metadata
        Raises:
            ValueError if provider is not specified or if extracted text is empty/whitespace
        """
        pass

