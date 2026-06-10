from abc import ABC, abstractmethod
from typing import List

from backend.apps.core.interfaces.job.i_message_job import IMessageJobContextHit

class IHybridSearchService(ABC):
    """Contract cho dịch vụ Tìm kiếm Lai (Hybrid Search Fusion)."""
    
    @abstractmethod
    def fuse_results(self, dense_hits: List[IMessageJobContextHit], sparse_hits: List[IMessageJobContextHit], top_k: int = 5) -> List[IMessageJobContextHit]:
        """Dung hợp kết quả từ Dense Vector (FAISS) và Sparse Vector (BM25)."""
        pass