"""
Hybrid search service module.
Combines semantic search (FAISS) and keyword search (BM25) results using RRF.
"""
from typing import List
from backend.apps.core.interfaces.job.i_message_job import IMessageJobContextHit
from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService

class HybridSearchService(IHybridSearchService):
    def __init__(self, locate_service, logger, rrf_k: int = 60):
        self.locate_service = locate_service
        self.logger = logger
        # rrf_k = 60 là tham số chuẩn hóa do Elasticsearch khuyến nghị cho RRF
        self.rrf_k = rrf_k

    def fuse_results(self, dense_hits: List[IMessageJobContextHit], sparse_hits: List[IMessageJobContextHit], top_k: int = 5) -> List[IMessageJobContextHit]:
        """Dung hợp kết quả từ Dense Vector (FAISS) và Sparse Vector (BM25)."""
        fused_scores = {}
        hit_map = {}

        # Tính điểm RRF cho FAISS (Dense)
        for rank, hit in enumerate(dense_hits):
            key = hit.text 
            fused_scores[key] = fused_scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            hit_map[key] = hit

        # Tính điểm RRF cho BM25 (Sparse)
        for rank, hit in enumerate(sparse_hits):
            key = hit.text
            fused_scores[key] = fused_scores.get(key, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            if key not in hit_map:
                hit_map[key] = hit

        # Sắp xếp lại theo điểm số Fused Score giảm dần
        sorted_fused = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)
        
        # Trả về top K kết quả
        results = []
        for key, score in sorted_fused[:top_k]:
            hit = hit_map[key]
            results.append(IMessageJobContextHit(
                text=hit.text, 
                score=score, 
                source_document_id=hit.source_document_id
            ))
            
        self.logger.info(f"Hybrid Fusion completed with {len(results)} results.", source=str(self.__class__))
        return results