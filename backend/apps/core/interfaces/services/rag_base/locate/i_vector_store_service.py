"""
Vector store interface module.
Abstract interface for vector storage operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from backend.apps.core.interfaces.response.i_vector_db_response import IVectorDBDeleteResponse, IVectorDBLoadResponse, IVectorDBQueryResponse, IVectorDBUpsertResponse


class IVectorStoreService(ABC):
    """
    Abstract interface for vector storage operations.
    Provider-agnostic interface for vector databases (Faiss, etc.).
    """

    @abstractmethod
    def create_index(self, np_vectors: np.ndarray, ids: np.ndarray = np.array([]), file_caller: str = "") -> Any:
        """
        Create vector index with specified dimension.

        Args:
            dimension: Dimensionality of the vectors to be indexed
            np_vectors: Optional initial vectors to add to the index
            file_caller: Identifier for the calling file
        Returns:
            Provider-specific index object or identifier
            Or Raise exception if index creation fails
        """
        pass

    @abstractmethod
    def upsert(
        self,
        index: Any,
        vector_id: str,
        file_caller: str = ""
    ) -> IVectorDBUpsertResponse:
        """
        Insert or update vector in store.
        Requires provider-specific index object or identifier to perform upsert operation, and vector_id for metadata and cache management.
        Args:
            index: Provider-specific index object or identifier
            vector_id: Unique identifier for vector
            dimension: Dimensionality of the vector
            np_vectors: Array of vector embeddings (list of floats)
            file_caller: Identifier for the calling file

        Returns:
            IVectorDBUpsertResponse with success status and additional info
            Or Raise exception if upsert fails
        """
        pass

    @abstractmethod
    def search(self, index: Any, vector_id: str, query_vector: np.ndarray, limit=5, 
               allow_ids: set | None = None, chunk_file_map: dict | None = None, file_caller: str = "") -> IVectorDBQueryResponse:
        """
        Perform similarity search.

        Args:
            index: Provider-specific index object or identifier
            vector_id: Unique identifier for the vector to search within (id for searching datablocks on cache)
            query_vector: Query embedding vector
            limit: Maximum number of results
            allow_ids: Optional set of allowed vector IDs
            chunk_file_map: Optional dictionary mapping chunks to files
            file_caller: Identifier for the calling file

        Returns:
            IVectorDBQueryResponse with search results and additional info
            Or Raise exception if search fails
        """
        pass

    @abstractmethod
    def delete(self, vector_id: str, file_caller: str = "") -> IVectorDBDeleteResponse:
        """
        Delete vector from store.

        Args:
            vector_id: Vector identifier
            file_caller: Identifier for the calling file

        Returns:
            IVectorDBDeleteResponse with success status and additional info
        """
        pass

    @abstractmethod
    def is_existed_in_metadata(self, vector_id: str, file_caller: str = "") -> Path | None:
        """
        Check if vector_id exists in metadata.

        Args:
            vector_id: Vector identifier to check.
            file_caller: Identifier for the calling file.
        Returns:
            Path to metadata file if exists, otherwise None.
        """
        pass

    @abstractmethod
    def load(self, vector_id: str, file_caller: str = "") -> IVectorDBLoadResponse:
        """
        Load vector into store and cache.

        Args:
            vector_id: Unique identifier for vector
            file_caller: Identifier for the calling file

        Returns:
            IVectorDBLoadResponse with success status and additional info
            Or Raise exception if load fails
        """
        pass
