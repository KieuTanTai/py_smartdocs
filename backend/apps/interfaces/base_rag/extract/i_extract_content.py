"""
Extract content service interface module.
Abstract interface for file content extraction orchestration.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.interfaces.base_rag.extract.i_ocr_response import IOCRResponse


class IExtractContent(ABC):
    """
    Abstract interface for content extraction.
    Orchestrates file extraction and content preparation.
    """

    @abstractmethod
    async def extract_from_file_text(self, file_path: Path) -> IOCRResponse:
        """
        Extract content from document file.

        Args:
            file_path: Path to document file

        Returns:
            IOCRResponse: Response object with extracted text and metadata
        """
        pass

    @abstractmethod
    async def extract_from_file_image(self, file_path: Path) -> IOCRResponse:
        """
        Extract image content.

        Args:
            file_path: Path to image file

        Returns:
            IOCRResponse: Response object with extracted text and metadata
        """
        pass
