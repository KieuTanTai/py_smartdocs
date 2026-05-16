"""
Indexing service interface module.
Abstract interface for vector indexing operations.
"""

from abc import ABC, abstractmethod


class IndexingServiceInterface(ABC):
    """
    Abstract interface for vector indexing.
    Indexes chunks with embeddings to vector store.
    """

    @abstractmethod
    async def index_document(self, document, chunks):
        """
        Index document chunks to vector store.

        Args:
            document: Document object
            chunks: List of Chunk objects with content

        Returns:
            IndexResult with chunk_count, collection_info, success status
        """
        pass

    @abstractmethod
    async def reindex_document(self, document):
        """
        Reindex existing document (delete and recreate).

        Args:
            document: Document object

        Returns:
            IndexResult from reindexing
        """
        pass

    @abstractmethod
    def prepare_index_payload(self, chunk, embedding, document_id):
        """
        Prepare chunk data for storage in vector store.

        Args:
            chunk: Chunk object
            embedding: Vector embedding
            document_id: Source document ID

        Returns:
            Payload dict ready for upsert
        """
        pass
