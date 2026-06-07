import hashlib
from pathlib import Path
from typing import List, Tuple

import numpy as np

from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.chunk.i_chunking import IChunking
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.core.normalize.i_normalize import INormalize
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.services.cache.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import IExtractContent
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.utils.hash_content import sha256_embedded_content


class UploadJob:
    """
    Job that orchestrates upload processing.

    Flow:
      1. Extract text from uploaded file
      2. Normalize text
      3. Chunk text and save chunks to cache
      4. Generate embedding vectors for all chunks
      5. Create and persist a FAISS index
    """

    def __init__(
        self,
        extract_service: IExtractContent,
        normalize: INormalize,
        chunker: IChunking,
        cache_session: IConnectCacheSession,
        llm_provider_factory: ILLMProviderFactory,
        locate_service: ILocateService,
        config_provider: IConfigProvider,
        logger: ILogger,
    ):
        self.extract_service = extract_service
        self.normalize = normalize
        self.chunker = chunker
        self.cache_session = cache_session
        self.llm_provider_factory = llm_provider_factory
        self.locate_service = locate_service
        self.config_provider = config_provider
        self.logger = logger

    def run(self, document_id: str, file_path: Path, provider: EProviderName) -> dict:
        if file_path is None or not file_path.exists():
            raise ValueError(f"File path does not exist: {file_path}")

        self.logger.info(
            f"Running upload job for document_id={document_id} and provider={provider}",
            source=str(self.__class__),
            method_call=self.run.__name__,
        )

        # 1. Extract content
        extracted_text = self.extract_service.extract_from_file_text(file_path, provider)
        if not extracted_text:
            raise ValueError("Extracted text is empty")

        # 2. Normalize
        normalized_text = self.normalize.normalize(extracted_text)

        # 3. Chunk + cache + generate ids
        chunk_texts = self.chunker.create_chunks(normalized_text)
        chunk_keys = self._build_chunk_keys(document_id, chunk_texts)
        cache_key = f"document_chunks:{document_id}"
        cache_metadata_key = f"{cache_key}:meta"
        cache_metadata = {
            "file_id": document_id,
            "chunks": {chunk_key: chunk_text for chunk_key, chunk_text in chunk_keys},
        }

        cache_service = self.cache_session.connect(file_caller=self.run.__name__)
        try:
            cache_service.set(cache_key, chunk_keys, file_caller=self.run.__name__)
            cache_service.set(cache_metadata_key, cache_metadata, file_caller=self.run.__name__)
        finally:
            self.cache_session.disconnect(file_caller=self.run.__name__)

        # 4. Embed all chunks
        embeddings = self._embed_chunk_texts(chunk_texts, provider)
        vectors = np.vstack(embeddings)
        vector_ids = self._build_vector_ids(document_id, len(chunk_texts))

        # 5. Save into vector store
        vector_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
        index = vector_store.create_index(vectors, vector_ids, file_caller=self.run.__name__)
        upsert_response = vector_store.upsert(index, vector_id=document_id, file_caller=self.run.__name__)

        file_key = sha256_embedded_content(vectors)

        return {
            "document_id": document_id,
            "cache_key": cache_key,
            "chunk_keys": [chunk_key for chunk_key, _ in chunk_keys],
            "vector_ids": vector_ids.tolist(),
            "file_key": file_key,
            "faiss_upsert": {
                "uuid": upsert_response.UUID,
                "is_success": upsert_response.is_success,
            },
        }

    def _build_chunk_keys(self, file_id: str, chunk_texts: List[str]) -> List[Tuple[str, str]]:
        return [(f"{file_id}:{sequence+1}", chunk_text) for sequence, chunk_text in enumerate(chunk_texts)]

    def _build_vector_ids(self, file_id: str, count: int) -> np.ndarray:
        base_hash = hashlib.sha256(file_id.encode("utf-8")).digest()[:8]
        base_id = int.from_bytes(base_hash, "big") & 0x7FFFFFFFFFFFFFFF
        return np.array([base_id + idx + 1 for idx in range(count)], dtype=np.int64)

    def _get_embedding_model(self, provider: EProviderName) -> str:
        providers = self.config_provider.get_list_providers()
        for provider_record in providers:
            if provider_record.provider_name == provider:
                return provider_record.embed_model_name
        raise ValueError(f"Embedding model not configured for provider {provider}")

    def _embed_chunk_texts(self, chunk_texts: List[str], provider: EProviderName) -> List[np.ndarray]:
        llm_client = self.llm_provider_factory.get_provider(provider)
        model_name = self._get_embedding_model(provider)
        embeddings = []
        for text in chunk_texts:
            response = llm_client.embedding(
                ICompletionRequest(provider=provider, model=model_name, prompt=text)
            )
            embeddings.append(response.embedding.astype(np.float32))
        return embeddings
