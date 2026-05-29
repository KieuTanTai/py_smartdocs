"""
Vector store interface module.
Abstract interface for vector storage operations.
"""

from abc import ABC, abstractmethod

import numpy as np

class IVectorStoreService(ABC):
    """
    Abstract interface for vector storage operations.
    Provider-agnostic interface for vector databases (Faiss, etc.).
    """

    @abstractmethod
    async def upsert(self, vector_id: str, vector: np.ndarray):
        """
        Insert or update vector in store.

        Args:
            vector_id: Unique identifier for vector
            vector: Vector embedding (list of floats)

        Returns:
            UpsertResult with success status
        """
        pass


    @abstractmethod
    async def search(self, query_vector: np.ndarray , limit=5, filters=None):
        """
        Perform similarity search.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional metadata filters

        Returns:
            List of SearchHit objects with vectors, scores, metadata
        """
        pass

    @abstractmethod


    @abstractmethod
    async def delete(self, vector_id):
        """
        Delete vector from store.

        Args:
            vector_id: Vector identifier

        Returns:
            Boolean success status
        """
        pass

    @abstractmethod
    async def get_collection_info(self):
        """
        Get collection statistics and info.

        Returns:
            Dict with vector_count, dimension, indexed_count, etc.
        """
        pass
