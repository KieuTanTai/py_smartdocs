"""
Chunking service interface module.
Abstract interface for text segmentation.
"""

from abc import ABC, abstractmethod


class ChunkingServiceInterface(ABC):
    """
    Abstract interface for text chunking.
    Segments normalized text into manageable chunks.
    """

    @abstractmethod
    async def create_chunks(self, normalized_document):
        """
        Create chunks from normalized text.

        Args:
            normalized_document: NormalizedDocument object

        Returns:
            List of Chunk objects with text, metadata, position
        """
        pass

    @abstractmethod
    def chunk_by_size(self, text, chunk_size, overlap):
        """
        Split text into fixed-size chunks with overlap.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Number of overlapping tokens between chunks

        Returns:
            List of text chunks
        """
        pass

    @abstractmethod
    def chunk_by_sentences(self, text, target_size):
        """
        Split text by sentences with target size.

        Args:
            text: Text to chunk
            target_size: Target chunk size in tokens/words

        Returns:
            List of sentence-based chunks
        """
        pass
