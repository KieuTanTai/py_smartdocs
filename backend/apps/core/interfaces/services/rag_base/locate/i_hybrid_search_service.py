"""
Hybrid search service interface module.
Abstract interface for hybrid search combining semantic and keyword retrieval.
"""

from abc import ABC, abstractmethod
from typing import List

import numpy as np


class IHybridSearchService(ABC):
    """
    Abstract interface for hybrid search service.
    
    Combines semantic search (FAISS) and keyword search (BM25) to provide
    comprehensive document retrieval with balanced relevance.
    """

    @abstractmethod
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
        Perform hybrid search combining FAISS and BM25 results.
        
        Args:
            document_id: Document ID to search within
            query_text: Query text string (for BM25)
            query_vector: Query embedding vector (for FAISS)
            limit: Maximum number of results
            faiss_weight: Weight for FAISS results (0-1), default 0.6
            bm25_weight: Weight for BM25 results (0-1), default 0.4
            allow_ids: Optional set of allowed chunk IDs to filter results
            chunk_file_map: Optional dict mapping chunks to files for filtering
            file_caller: Identifier for the calling file/function
            
        Returns:
            Dict with structure:
            {
                "results": [
                    {
                        "chunk_id": str,
                        "score": float (weighted score 0-1),
                        "sources": list (["faiss", "bm25"] or subset),
                        "faiss_score": float,
                        "bm25_score": float
                    },
                    ...
                ],
                "faiss_results": [...],  # Raw FAISS results
                "bm25_results": [...]    # Raw BM25 results
            }
            
        Raises:
            ValueError: If document_id not found or search fails
        """
        pass
