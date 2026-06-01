"""
Extract content service interface module.
Abstract interface for file content extraction orchestration.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionResponse
from sys_services.enums.e_provider_name import EProviderName


class IExtractContent(ABC):
    """
    Abstract interface for content extraction.
    Orchestrates file extraction and content preparation.
    """

    @abstractmethod
    async def extract_from_file_text(
        self,
        file_path: Path,
        provider: EProviderName,
    ) -> ICompletionResponse:
        """
        Extract content from document file.

        Args:
            file_path: Path to document file
            provider: LLM provider to use for OCR extraction

        Returns:
            ICompletionResponse: Response object with extracted text and metadata
        """
        pass

    @abstractmethod
    async def extract_from_file_image(
        self,
        file_path: Path,
        provider: EProviderName,
    ) -> ICompletionResponse:
        """
        Extract image content.

        Args:
            file_path: Path to image file
            provider: LLM provider to use for OCR extraction

        Returns:
            ICompletionResponse: Response object with extracted text and metadata
        """
        pass
