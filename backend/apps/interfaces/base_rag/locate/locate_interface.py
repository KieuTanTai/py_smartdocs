"""
Locate service interface module.
Abstract interface for chunk and document location tracking.
"""

from abc import ABC, abstractmethod


class LocateServiceInterface(ABC):
    """
    Abstract interface for locating documents and chunks.
    Manages relationships between chunks and source documents.
    """

    @abstractmethod
    async def locate_chunk(self, chunk_id):
        """
        Find location and source document for a chunk.

        Args:
            chunk_id: Chunk identifier

        Returns:
            ChunkLocation with document_id, position, context
        """
        pass

    @abstractmethod
    async def get_document_chunks(self, document_id):
        """
        Retrieve all chunks for a specific document.

        Args:
            document_id: Document identifier

        Returns:
            List of chunks with metadata
        """
        pass

    @abstractmethod
    def get_chunk_source_info(self, chunk):
        """
        Extract source document info from chunk metadata.

        Args:
            chunk: Chunk object

        Returns:
            Dict with source document information
        """
        pass
