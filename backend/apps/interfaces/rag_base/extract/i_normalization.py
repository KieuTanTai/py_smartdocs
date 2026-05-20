"""
Normalization service interface module.
Abstract interface for document text normalization.
"""

from abc import ABC, abstractmethod


class INormalization(ABC):
    """
    Abstract interface for text normalization.
    Preprocessing stage before chunking and indexing.
    """

    @abstractmethod
    async def normalize_document(self, document):
        """
        Normalize document text.

        Args:
            document: Document object with raw content

        Returns:
            NormalizedDocument with normalized_text, metadata, content_hash
        """
        pass

    @abstractmethod
    def remove_excess_whitespace(self, text):
        """
        Standardize whitespace and line endings.

        Args:
            text: Raw text

        Returns:
            Normalized text
        """
        pass

    @abstractmethod
    def preserve_paragraphs(self, text):
        """
        Maintain readable paragraph structure.

        Args:
            text: Text to process

        Returns:
            Text with preserved paragraph boundaries
        """
        pass
