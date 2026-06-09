"""
BM25 vector store service module.
"""

import datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import (
    IVectorStoreService,
)
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.response.i_vector_db_response import (
    IVectorDBDeleteResponse,
    IVectorDBLoadResponse,
    IVectorDBQueryResponse,
    IVectorDBUpsertResponse,
)
from backend.apps.utils.path_file_helper import (
    create_path_file,
    delete_file_metadata_with_file_name,
    is_existed_in_metadata,
)


class BM25Service(IVectorStoreService):
    """
    BM25 service for keyword-based retrieval (lexical search).
    
    Uses rank_bm25 (BM25Okapi algorithm) for proper BM25 scoring.
    Stores indexed texts and corpus metadata in JSON format.
    Provides a complement to semantic search (FAISS).
    """

    def __init__(
        self,
        metadata_dir: Path,
        logger: ILogger,
    ):
        self.metadata_dir = metadata_dir / "bm25"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        # In-memory BM25 indexes: {vector_id -> BM25Okapi instance}
        self._bm25_indexes = {}

    def create_index(
        self, np_vectors: np.ndarray = np.array([]), ids: np.ndarray = np.array([]), file_caller: str = ""
    ) -> dict:
        """
        Create BM25 index. BM25 uses text corpus, not vectors.
        
        Args:
            np_vectors: Not used for BM25 (kept for interface compatibility)
            ids: Not used for BM25
            file_caller: Identifier for the calling file
            
        Returns:
            Empty dict as placeholder (BM25 doesn't need vector index creation)
        """
        self.logger.info(
            "Creating BM25 index",
            Path(__file__).name,
            file_caller,
            method_call=self.create_index.__name__,
        )
        return {}

    def upsert(
        self, index: Any, vector_id: str, file_caller: str = ""
    ) -> IVectorDBUpsertResponse:
        """
        Save BM25 metadata (texts and corpus) for vector_id.
        
        Args:
            index: Dict with chunk texts: {chunk_id: text}
            vector_id: Document ID
            file_caller: Identifier for calling file
            
        Returns:
            IVectorDBUpsertResponse with success status
        """
        self.__write_metadata_file(vector_id, index)
        self.logger.info(
            f"Upserted BM25 index for vector_id '{vector_id}' with {len(index)} chunks",
            Path(__file__).name,
            file_caller,
            method_call=self.upsert.__name__,
        )
        return IVectorDBUpsertResponse(
            UUID=vector_id,
            create_at=datetime.datetime.now(),
            sumarize_content="",
            is_success=True,
        )

    def search(
        self,
        index: Any,
        vector_id: str,
        query_vector: np.ndarray,
        limit=5,
        allow_ids: set | None = None,
        chunk_file_map: dict | None = None,
        file_caller: str = "",
    ) -> IVectorDBQueryResponse:
        """
        BM25 keyword search using rank_bm25 algorithm.
        
        Args:
            index: BM25 index (dict with texts, or empty - will load from disk)
            vector_id: Document ID to search within
            query_vector: Query text (as np.ndarray or string)
            limit: Max results
            allow_ids: Filter by allowed chunk IDs
            chunk_file_map: Filter by chunk-file mapping
            file_caller: Identifier for calling file
            
        Returns:
            IVectorDBQueryResponse with search results and BM25 scores
        """
        # Load texts from metadata
        texts_map = self.__load_texts_for_vector(vector_id, file_caller)

        if not texts_map:
            self.logger.warning(
                f"No texts found for BM25 search on vector_id '{vector_id}'",
                Path(__file__).name,
                file_caller,
                method_call=self.search.__name__,
            )
            return IVectorDBQueryResponse(
                UUID=vector_id, distances=[], indices=[]
            )

        # Convert query_vector to string
        if isinstance(query_vector, np.ndarray):
            if query_vector.dtype == object:
                query_text = query_vector[0] if len(query_vector) > 0 else ""
            else:
                query_text = str(query_vector)
        else:
            query_text = str(query_vector)

        # Tokenize query
        query_tokens = query_text.lower().split()
        if not query_tokens:
            return IVectorDBQueryResponse(
                UUID=vector_id, distances=[], indices=[]
            )

        # Build BM25 index from corpus
        corpus = list(texts_map.values())
        corpus_tokens = [text.lower().split() for text in corpus]
        bm25 = BM25Okapi(corpus_tokens)

        # Score all documents
        scores = bm25.get_scores(query_tokens)
        
        # Create results with chunk IDs and scores
        results = []
        for chunk_id, text in texts_map.items():
            # Find score for this chunk
            chunk_idx = list(texts_map.keys()).index(chunk_id)
            score = float(scores[chunk_idx])
            
            # Apply filters
            if allow_ids is not None and chunk_id not in allow_ids:
                continue
            if chunk_file_map is not None and chunk_file_map.get(chunk_id) is None:
                continue
                
            results.append((chunk_id, score))

        # Sort by score descending, take top-k
        results.sort(key=lambda x: x[1], reverse=True)
        ranked = results[:limit]
        
        indices = [idx for idx, _ in ranked]
        distances = [score for _, score in ranked]

        self.logger.info(
            f"BM25 search results for vector_id '{vector_id}': {len(indices)} results, query='{query_text}'",
            Path(__file__).name,
            file_caller,
            method_call=self.search.__name__,
        )
        return IVectorDBQueryResponse(
            UUID=vector_id, distances=distances, indices=indices
        )

    def delete(self, vector_id: str, file_caller: str = "") -> IVectorDBDeleteResponse:
        """Delete BM25 metadata for vector_id."""
        deleted_count = delete_file_metadata_with_file_name(
            self.metadata_dir, vector_id, "bm25", self.logger
        )
        if deleted_count == 0:
            self.logger.warning(
                f"BM25 index with id '{vector_id}' does not exist",
                Path(__file__).name,
                file_caller,
                method_call=self.delete.__name__,
            )
            return IVectorDBDeleteResponse(
                UUID=vector_id,
                is_success=False,
                message=f"BM25 index with id '{vector_id}' not found",
            )
        self.logger.info(
            f"Deleted BM25 index for vector_id '{vector_id}'",
            Path(__file__).name,
            file_caller,
            method_call=self.delete.__name__,
        )
        return IVectorDBDeleteResponse(UUID=vector_id, is_success=True, deleted_count=deleted_count)

    def load(self, vector_id: str, file_caller: str = "") -> IVectorDBLoadResponse:
        """Load BM25 index from metadata."""
        path = self.is_existed_in_metadata(vector_id)
        if path is None:
            self.logger.error(
                f"BM25 metadata for vector_id '{vector_id}' not found",
                Path(__file__).name,
                file_caller,
                method_call=self.load.__name__,
            )
            raise ValueError(f"BM25 index with id '{vector_id}' not found")
        
        with open(path, "r", encoding="utf-8") as f:
            texts_map = json.load(f)
        
        self.logger.info(
            f"Loaded BM25 index for vector_id '{vector_id}' with {len(texts_map)} chunks",
            Path(__file__).name,
            file_caller,
            method_call=self.load.__name__,
        )
        return IVectorDBLoadResponse(
            UUID=vector_id, is_success=True, index=texts_map
        )

    def is_existed_in_metadata(self, vector_id: str) -> Path | None:
        """Check if BM25 metadata exists."""
        return is_existed_in_metadata(self.metadata_dir, vector_id, "bm25", self.logger)

    # Private methods
    def __write_metadata_file(self, vector_id: str, texts_map: dict) -> None:
        """Write BM25 texts metadata to file."""
        metadata_path = create_path_file(self.metadata_dir, vector_id, "bm25", self.logger)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(texts_map, f, indent=2, ensure_ascii=False)

    def __load_texts_for_vector(self, vector_id: str, file_caller: str = "") -> dict:
        """Load text map from metadata."""
        try:
            path = self.is_existed_in_metadata(vector_id)
            if path is None:
                return {}
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(
                f"Error loading BM25 texts: {e}",
                Path(__file__).name,
                file_caller,
            )
            return {}
