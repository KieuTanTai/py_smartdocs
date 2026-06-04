"""
Locate service interface module.
Abstract interface for chunk and document location tracking.
"""

from abc import ABC, abstractmethod

from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName


class ILocateService(ABC):
    """
        Abstract interface for get and using instance of vector storage services or graph databases

    """
    @abstractmethod
    def get_vector_store(self, backend: EBackendStorageName) -> IVectorStoreService:
        """Get vector store service instance based on backend name.
        Args:
            backend: Name of vector store backend (e.g., "faiss")
        Returns:
            IVectorStoreService instance for specified backend
        """
        pass

    # @abstractmethod
    # def get_graph_db(self, backend: EBackendStorageName) -> IGraphDBService:
    #     """Get graph database service instance based on backend name.
    #     Args:
    #         backend: Name of graph database backend (e.g., "neo4j", "arangodb")
    #     Returns:
    #         IGraphDBService instance for specified backend
    #     """
    #     pass