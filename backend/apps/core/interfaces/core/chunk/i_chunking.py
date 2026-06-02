"""
Chunking service interface module.
Abstract interface for text segmentation.
"""

from abc import ABC, abstractmethod


class IChunking(ABC):
    """
    Abstract interface for text chunking.
    Segments normalized text into manageable chunks.
    """

    @abstractmethod
    def create_chunks(self, normalized_document: str) -> list[str]:
        """
        Create chunks from normalized text.

        Args:
            normalized_document: NormalizedDocument object

        Returns:
            List of Chunk objects with text, metadata, position
        """
        pass
