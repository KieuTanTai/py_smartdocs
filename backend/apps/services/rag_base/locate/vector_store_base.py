import json
from pathlib import Path
from typing import Sequence

import numpy as np

from backend.apps.core.interfaces.services.rag_base.locate.i_embed_storage_result import IEmbeddingStorageResult
from backend.apps.utils.is_path_valiable import (
    check_storage_dir_exists_and_accessible,
)
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER

EmbeddingInput = Sequence[float] | Sequence[Sequence[float]] | np.ndarray



class VectorStoreBase:
    def __init__(
        self,
        storage_dir: Path | None = None,
        metadata_dir: Path | None = None,
        logger: ILogger | None = None,
    ):
        self.storage_dir = storage_dir or Path("storage")
        self.metadata_dir = metadata_dir or Path("metadata")
        self.logger = logger or DEFAULT_LOGGER

    def save_embedding_with_metadata(
        self,
        backend_name: str,
        embed_id: str,
        embeddings: EmbeddingInput,
    ) -> IEmbeddingStorageResult:
        if not embed_id:
            raise ValueError("embed_id is required")

        embedding_matrix = self._normalize_embeddings(embeddings)
        storage_dir = self.storage_dir / backend_name
        metadata_dir = self.metadata_dir / backend_name

        check_storage_dir_exists_and_accessible(storage_dir, self.logger)
        check_storage_dir_exists_and_accessible(metadata_dir, self.logger)

        embedding_path = storage_dir / f"{embed_id}.npy"
        np.save(embedding_path, embedding_matrix)

        metadata = {
            "id": embed_id,
            "storage_path": str(embedding_path),
            "vector_count": int(embedding_matrix.shape[0]),
            "dimension": int(embedding_matrix.shape[1]),
        }
        metadata_path = metadata_dir / embed_id
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

        self.logger.info(
            f"Saved embedding '{embed_id}' to {embedding_path}",
            source=str(self.__class__),
        )
        self.logger.info(
            f"Saved embedding metadata '{embed_id}' to {metadata_path}",
            source=str(self.__class__),
        )

        return IEmbeddingStorageResult(
            embedding_path=embedding_path,
            metadata_path=metadata_path,
            vector_count=int(embedding_matrix.shape[0]),
            dimension=int(embedding_matrix.shape[1]),
        )

    def _normalize_embeddings(self, embeddings: EmbeddingInput) -> np.ndarray:
        embedding_matrix = np.asarray(embeddings, dtype=np.float32)
        if embedding_matrix.ndim == 1:
            embedding_matrix = embedding_matrix.reshape(1, -1)
        if embedding_matrix.ndim != 2:
            raise ValueError("embeddings must be a 1D or 2D array of floats")
        if embedding_matrix.shape[1] == 0:
            raise ValueError("embedding dimension must be greater than 0")
        return embedding_matrix
