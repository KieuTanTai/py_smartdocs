"""
Hybrid search service module.
Combines semantic search (FAISS) and keyword search (BM25) results.
"""

from typing import List

import numpy as np

from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.interfaces.services.rag_base.locate.i_hybrid_search_service import IHybridSearchService
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.system.i_logging import ILogger


class HybridSearchService(IHybridSearchService):
    """
    Hybrid search implementation combining FAISS (semantic) and BM25 (keyword) results.
    
    Strategy:
    1. Execute FAISS search to get top-k semantic results
    2. Execute BM25 search to get top-k keyword results
    3. Merge and rank results using weighted scoring
    """

    def __init__(self, locate_service: ILocateService, logger: ILogger):
        self.locate_service = locate_service
        self.logger = logger

    def search(
        self,
        document_id: str,
        query_text: str,
        query_vector: np.ndarray,
        limit: int = 5,
        faiss_weight: float = 0.6,
        bm25_weight: float = 0.4,
        allow_ids: set | None = None,
        chunk_file_map: dict | None = None,
        file_caller: str = "",
    ) -> dict:
        """
        Perform hybrid search (FAISS + BM25).
        
        Args:
            document_id: Document ID to search within
            query_text: Query text string (for BM25)
            query_vector: Query embedding vector (for FAISS)
            limit: Maximum number of results
            faiss_weight: Weight for FAISS results (0-1)
            bm25_weight: Weight for BM25 results (0-1)
            allow_ids: Optional set of allowed chunk IDs
            chunk_file_map: Optional dict mapping chunks to files
            file_caller: Identifier for calling file
            
        Returns:
            {
                "results": [{"chunk_id": str, "score": float, "source": str}, ...],
                "faiss_results": [...],
                "bm25_results": [...]
            }
        """
        self.logger.info(
            f"Starting hybrid search for document_id='{document_id}', query_text='{query_text[:50]}...'",
            source=str(self.__class__),
        )

        # FAISS search (semantic)
        faiss_results = self.__faiss_search(
            document_id,
            query_vector,
            limit,
            allow_ids,
            chunk_file_map,
            file_caller,
        )

        # BM25 search (keyword)
        bm25_results = self.__bm25_search(
            document_id,
            query_text,
            limit,
            allow_ids,
            chunk_file_map,
            file_caller,
        )

        # Merge and rank results
        merged_results = self.__merge_results(
            faiss_results,
            bm25_results,
            faiss_weight,
            bm25_weight,
            limit,
        )

        self.logger.info(
            f"Hybrid search completed: {len(merged_results)} results",
            source=str(self.__class__),
        )

        return {
            "results": merged_results,
            "faiss_results": faiss_results,
            "bm25_results": bm25_results,
        }

    # Private methods
    def __faiss_search(
        self,
        document_id: str,
        query_vector: np.ndarray,
        limit: int,
        allow_ids: set | None,
        chunk_file_map: dict | None,
        file_caller: str,
    ) -> List[dict]:
        """Execute FAISS semantic search."""
        try:
            faiss_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
            faiss_response = faiss_store.search(
                index={},  # FAISS loads index internally
                vector_id=document_id,
                query_vector=query_vector,
                limit=limit,
                allow_ids=allow_ids,
                chunk_file_map=chunk_file_map,
                file_caller=file_caller,
            )

            # Convert FAISS results to dict format
            results = [
                {"chunk_id": str(idx), "distance": float(dist), "source": "faiss"}
                for idx, dist in zip(faiss_response.indices, faiss_response.distances)
            ]
            self.logger.info(f"FAISS search: {len(results)} results", source=str(self.__class__))
            return results
        except Exception as e:
            self.logger.error(
                f"FAISS search failed: {e}",
                source=str(self.__class__),
            )
            return []

    def __bm25_search(
        self,
        document_id: str,
        query_text: str,
        limit: int,
        allow_ids: set | None,
        chunk_file_map: dict | None,
        file_caller: str,
    ) -> List[dict]:
        """Execute BM25 keyword search."""
        try:
            bm25_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)
            # Convert query_text to np.ndarray for interface compatibility
            query_vector = np.array([query_text], dtype=object)
            bm25_response = bm25_store.search(
                index={},  # BM25 loads index internally
                vector_id=document_id,
                query_vector=query_vector,
                limit=limit,
                allow_ids=allow_ids,
                chunk_file_map=chunk_file_map,
                file_caller=file_caller,
            )

            # Convert BM25 results to dict format
            results = [
                {"chunk_id": str(idx), "score": float(score), "source": "bm25"}
                for idx, score in zip(bm25_response.indices, bm25_response.distances)
            ]
            self.logger.info(f"BM25 search: {len(results)} results", source=str(self.__class__))
            return results
        except Exception as e:
            self.logger.error(
                f"BM25 search failed: {e}",
                source=str(self.__class__),
            )
            return []

    def __merge_results(
        self,
        faiss_results: List[dict],
        bm25_results: List[dict],
        faiss_weight: float,
        bm25_weight: float,
        limit: int,
    ) -> List[dict]:
        """
        Merge FAISS and BM25 results with weighted scoring.
        
        Normalize scores and combine using weights.
        """
        # Normalize FAISS distances (lower is better, convert to similarity score)
        faiss_max_dist = max([r["distance"] for r in faiss_results], default=1.0)
        faiss_normalized = [
            {
                "chunk_id": r["chunk_id"],
                "score": (1 - r["distance"] / faiss_max_dist) if faiss_max_dist > 0 else 0,
                "source": "faiss",
            }
            for r in faiss_results
        ]

        # Normalize BM25 scores (higher is better)
        bm25_max_score = max([r["score"] for r in bm25_results], default=1.0)
        bm25_normalized = [
            {
                "chunk_id": r["chunk_id"],
                "score": r["score"] / bm25_max_score if bm25_max_score > 0 else 0,
                "source": "bm25",
            }
            for r in bm25_results
        ]

        # Merge by chunk_id
        chunk_scores = {}
        for result in faiss_normalized:
            chunk_id = result["chunk_id"]
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = {"faiss": 0, "bm25": 0, "sources": set()}
            chunk_scores[chunk_id]["faiss"] = result["score"]
            chunk_scores[chunk_id]["sources"].add("faiss")

        for result in bm25_normalized:
            chunk_id = result["chunk_id"]
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = {"faiss": 0, "bm25": 0, "sources": set()}
            chunk_scores[chunk_id]["bm25"] = result["score"]
            chunk_scores[chunk_id]["sources"].add("bm25")

        # Calculate hybrid score
        hybrid_results = [
            {
                "chunk_id": chunk_id,
                "score": scores["faiss"] * faiss_weight + scores["bm25"] * bm25_weight,
                "sources": list(scores["sources"]),
                "faiss_score": scores["faiss"],
                "bm25_score": scores["bm25"],
            }
            for chunk_id, scores in chunk_scores.items()
        ]

        # Sort by hybrid score and return top-k
        hybrid_results.sort(key=lambda x: x["score"], reverse=True)
        return hybrid_results[:limit]
