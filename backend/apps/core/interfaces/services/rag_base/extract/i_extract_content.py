"""
Extract content service interface module.
Abstract interface for file content extraction orchestration.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.core.enums.e_provider_name import EProviderName
from mistralai.client.models import OCRResponse

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
    ) -> OCRResponse:
        """
        Extract content from file.

        Args:
            file_path: Path to file
            provider: LLM provider to use for OCR extraction

        Returns:
            OCRResponse: Response object with extracted text and metadata
        """
        pass

