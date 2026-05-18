"""
Extract content service interface module.
Abstract interface for file content extraction orchestration.
"""

from abc import ABC, abstractmethod


class ExtractContentInterface(ABC):
    """
    Abstract interface for content extraction.
    Orchestrates file extraction and content preparation.
    """

    @abstractmethod
    async def extract_from_file(self, document):
        """
        Extract content from document file.

        Args:
            document: Document object with file_path

        Returns:
            ExtractionResult with raw_text, metadata, errors
        """
        pass

    @abstractmethod
    def get_extractor_for_file(self, mime_type):
        """
        Select appropriate extractor by file type.

        Args:
            mime_type: File MIME type

        Returns:
            ExtractorInterface implementation
        """
        pass

    @abstractmethod
    async def extract_text(self, file_path):
        """
        Extract plain text content.

        Args:
            file_path: Path to text file

        Returns:
            Text content
        """
        pass

    @abstractmethod
    async def extract_pdf(self, file_path):
        """
        Extract PDF content with optional OCR.

        Args:
            file_path: Path to PDF file

        Returns:
            PDF content and text
        """
        pass
