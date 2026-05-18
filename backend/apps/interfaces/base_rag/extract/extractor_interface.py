"""
Extractor interface module.
Abstract interface for file content extraction.
"""

from abc import ABC, abstractmethod


class ExtractorInterface(ABC):
    """
    Abstract interface for file extraction.
    Handles extracting content from various file formats.
    """

    @abstractmethod
    async def extract(self, file_path):
        """
        Extract content from file.

        Args:
            file_path: Path to file in storage

        Returns:
            ExtractionResult with raw_text and metadata
        """
        pass

    @abstractmethod
    async def extract_metadata(self, file_path):
        """
        Extract file metadata (title, author, pages, etc.).

        Args:
            file_path: Path to file in storage

        Returns:
            Dict with metadata fields
        """
        pass

    @abstractmethod
    def is_supported(self, file_extension):
        """
        Check if file format is supported.

        Args:
            file_extension: File extension (e.g., 'pdf', 'txt')

        Returns:
            Boolean support status
        """
        pass
