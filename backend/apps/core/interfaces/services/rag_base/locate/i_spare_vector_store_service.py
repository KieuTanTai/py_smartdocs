from abc import ABC, abstractmethod
from typing import Any

from backend.apps.core.interfaces.response.i_vector_db_response import IVectorDBDeleteResponse, IVectorDBLoadResponse, IVectorDBQueryResponse, IVectorDBUpsertResponse
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_db_service import IVectorDBService


class ISpareVectorStoreService(IVectorDBService, ABC):

    @abstractmethod
    def upsert(
        self, index: dict[str, str], vector_id: str, file_caller: str = ""
    ) -> IVectorDBUpsertResponse:
        """Insert or update vector in store.
        Requires provider-specific index object or identifier to perform upsert operation, and vector_id for metadata and cache management.
        Args:
            index: Provider-specific index object or identifier
            vector_id: Unique identifier for vector
            file_caller: Identifier for the calling file
        Returns:
            IVectorDBUpsertResponse with success status and additional info
            Or Raise exception if upsert fails
        """
        pass

    @abstractmethod
    def search(
        self,
        index: Any,
        vector_id: str,
        query_text: str,
        limit: int = 5,
        file_caller: str = "",
    ) -> IVectorDBQueryResponse:
        """Perform similarity search.
        Args:
            index: Provider-specific index object or identifier
            vector_id: Unique identifier for the vector to search within (id for searching datablocks on cache)
            query_text: Text query for searching
            limit: Maximum number of results
            file_caller: Identifier for the calling file
        Returns:
            IVectorDBQueryResponse with search results and additional info
            Or Raise exception if search fails
        """
        pass

    @abstractmethod
    def load(self, vector_id: str, file_caller: str = "") -> IVectorDBLoadResponse:
        pass

    @abstractmethod
    def delete(self, vector_id: str, file_caller: str = "") -> IVectorDBDeleteResponse:
        pass
