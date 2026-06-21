"""
Interface for Delete Job module.
"""

from abc import ABC, abstractmethod
from typing import List

class IDeleteJob(ABC):
    """
    Contract for Document Deletion Processing across all Vector and Graph databases.
    """
    
    @abstractmethod
    def step_delete_vectors(self, document_id: str, file_caller: str = "") -> bool:
        """
        Xóa Vector Index trong FAISS và BM25.
        """
        pass

    @abstractmethod
    def step_delete_graph_data(self, document_id: str, file_caller: str = "") -> bool:
        """
        Xóa Đồ thị tri thức (Knowledge Graph) và Vector Index trong Neo4j.
        """
        pass

    @abstractmethod
    def step_clear_cache(self, document_id: str, file_caller: str = "") -> bool:
        """
        Xóa dữ liệu thô (Chunk text) đã lưu trong Redis Cache.
        """
        pass
    
    @abstractmethod
    def step_delete_cloud_file(self, file_id: str, file_caller: str = "") -> bool:
        """
        Xóa file tạm trên Cloud của LLM Provider (Mistral Cloud).
        """
        pass