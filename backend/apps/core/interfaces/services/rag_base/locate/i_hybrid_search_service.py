from abc import ABC, abstractmethod
from typing import List
from backend.apps.interfaces.job.i_message_job import ContextHit

class IHybridSearchService(ABC):
    """Contract cho dịch vụ Tìm kiếm Lai (Hybrid Search Fusion)."""
    
    @abstractmethod
    def fuse_results(self, dense_hits: List[ContextHit], sparse_hits: List[ContextHit], top_k: int = 5) -> List[ContextHit]:
        """Dung hợp kết quả từ Dense Vector (FAISS) và Sparse Vector (BM25)."""
        pass