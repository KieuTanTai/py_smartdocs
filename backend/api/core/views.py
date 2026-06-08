"""
Core search endpoint: cross-document vector search.
POST /api/core/search/
Searches all indexed documents for query-relevant chunks.
"""
from __future__ import annotations

import json
import time
from typing import Optional

import numpy as np
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.services.chat.models import DocumentModel
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.services.rag_base.locate.locate_service import LocateService
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.system_dirs import METADATA_DIR


def _embed_query(query: str) -> np.ndarray:
    factory = LLMProviderFactory(DEFAULT_CONFIG_PROVIDER, DEFAULT_LOGGER)
    client = factory.get_provider(EProviderName.GEMINI)
    req = ICompletionRequest(
        provider=EProviderName.GEMINI,
        model="gemini-embedding-2",
        prompt=query,
    )
    resp = client.embedding(req)
    return resp.embedding.reshape(1, -1).astype(np.float32)


def _search_all_documents(
    query_vector: np.ndarray,
    top_k: int = 10,
) -> list[dict]:
    """
    Search across ALL indexed documents in the system.
    Returns list of result dicts with text, score, document metadata.
    """
    locate_service = LocateService(metadata_dir=METADATA_DIR, logger=DEFAULT_LOGGER)
    faiss_service = locate_service.get_vector_store(EBackendStorageName.FAISS)

    indexed_docs = DocumentModel.objects.filter(status="indexed")
    all_results: list[dict] = []

    for doc in indexed_docs:
        vector_id = str(doc.faiss_index_id)
        try:
            load_resp = faiss_service.load(vector_id)
            index = load_resp.index
        except ValueError:
            continue

        search_resp = faiss_service.search(
            index=index,
            vector_id=vector_id,
            query_vector=query_vector,
            limit=top_k,
        )

        # Load chunk metadata
        metadata_path = METADATA_DIR / "docs" / f"{vector_id}.json"
        chunk_texts: dict[int, str] = {}
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                chunk_texts = {int(k): v for k, v in meta.get("chunks", {}).items()}

        for dist, idx in zip(search_resp.distances, search_resp.indices):
            if idx in chunk_texts:
                all_results.append({
                    "document_id": vector_id,
                    "document_title": doc.faiss_index_file_name,
                    "chunk_idx": int(idx),
                    "text": chunk_texts[idx],
                    "score": round(float(dist), 4),
                    "status": doc.status,
                })

    # Sort by score (ascending distance = more similar)
    all_results.sort(key=lambda x: x["score"])
    return all_results[:top_k]


class CoreSearchView(APIView):
    """
    POST /api/core/search/
    Body: { "query": "...", "top_k": 10 }
    Returns: { "results": [...], "total": int, "query": str }
    """

    def post(self, request):
        query = (request.data.get("query") or "").strip()
        top_k = min(int(request.data.get("top_k", 10)), 50)

        if not query:
            return Response(
                {"error": "Query is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start = time.time()
            query_vector = _embed_query(query)
            results = _search_all_documents(query_vector, top_k=top_k)
            elapsed_ms = int((time.time() - start) * 1000)

            return Response({
                "query": query,
                "total": len(results),
                "results": results,
                "metrics": {
                    "elapsed_ms": elapsed_ms,
                    "top_k": top_k,
                },
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            DEFAULT_LOGGER.error(
                f"Core search failed: {exc}",
                source="CoreSearchView",
            )
            return Response(
                {"error": f"Search failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
