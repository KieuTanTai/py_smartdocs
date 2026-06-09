import hashlib
from pathlib import Path
from typing import List, Tuple
import numpy as np

# Import Interface và DTO
from backend.apps.interfaces.job.i_upload_job import (
    IUploadJob, ChunkAndCacheResponse, EmbedAndSaveResponse, VectorStoreUpsertStatus
)
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


class UploadJob(IUploadJob): # <--- Kế thừa Interface
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

    def step_extract(self, file_path: Path, provider: EProviderName) -> str:
        # Code implement y hệt như đã tối ưu ở version trước
        extracted_text = self.extract_service.extract_from_file_text(file_path, provider)
        if not extracted_text:
            raise ValueError(f"Extracted text from {file_path.name} is empty.")
        return extracted_text

    def step_normalize(self, raw_text: str) -> str:
        return self.normalize.normalize(raw_text)

    def step_chunk_and_cache(self, document_id: str, normalized_text: str) -> ChunkAndCacheResponse:
        chunk_texts = self.chunker.create_chunks(normalized_text)
        chunk_keys_tuples = self._build_chunk_keys(document_id, chunk_texts)
        
        cache_key = f"document_chunks:{document_id}"
        cache_metadata_key = f"{cache_key}:meta"
        
        cache_metadata = {
            "file_id": document_id,
            "chunks": {chunk_key: chunk_text for chunk_key, chunk_text in chunk_keys_tuples},
        }

        cache_service = self.cache_session.connect(file_caller=self.step_chunk_and_cache.__name__)
        try:
            cache_service.set(cache_key, chunk_keys_tuples, file_caller=self.step_chunk_and_cache.__name__)
            cache_service.set(cache_metadata_key, cache_metadata, file_caller=self.step_chunk_and_cache.__name__)
        finally:
            self.cache_session.disconnect(file_caller=self.step_chunk_and_cache.__name__)

        return ChunkAndCacheResponse(
            document_id=document_id,
            cache_key=cache_key,
            chunk_keys=[k for k, _ in chunk_keys_tuples],
            chunk_texts=chunk_texts
        )

    def step_embed_and_save(self, chunk_data: ChunkAndCacheResponse, provider: EProviderName) -> EmbedAndSaveResponse:
        document_id = chunk_data.document_id
        chunk_keys = chunk_data.chunk_keys
        chunk_texts = chunk_data.chunk_texts

        embeddings = self._embed_chunk_texts(chunk_texts, provider)
        vectors = np.vstack(embeddings)
        vector_ids = self._build_vector_ids(document_id, len(chunk_texts))

        faiss_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
        faiss_index = faiss_store.create_index(vectors, vector_ids, file_caller=self.step_embed_and_save.__name__)
        faiss_upsert = faiss_store.upsert(faiss_index, vector_id=document_id, file_caller=self.step_embed_and_save.__name__)

        bm25_texts_map = {str(k): v for k, v in zip(chunk_keys, chunk_texts)}
        bm25_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)
        bm25_index = bm25_store.create_index(file_caller=self.step_embed_and_save.__name__)
        bm25_upsert = bm25_store.upsert(bm25_texts_map, vector_id=document_id, file_caller=self.step_embed_and_save.__name__)

        file_key = sha256_embedded_content(vectors)

        return EmbedAndSaveResponse(
            document_id=document_id,
            file_key=file_key,
            vector_ids=vector_ids.tolist(),
            faiss_upsert=VectorStoreUpsertStatus(uuid=faiss_upsert.UUID, is_success=faiss_upsert.is_success),
            bm25_upsert=VectorStoreUpsertStatus(uuid=bm25_upsert.UUID, is_success=bm25_upsert.is_success)
        )

    # --- PRIVATE HELPERS GỐC (GIỮ NGUYÊN) ---

    def _build_chunk_keys(self, file_id: str, chunk_texts: List[str]) -> List[Tuple[str, str]]:
        """Sinh key cấu trúc dạng (file_id:chunk_index)"""
        return [(f"{file_id}:{sequence+1}", chunk_text) for sequence, chunk_text in enumerate(chunk_texts)]

    def _build_vector_ids(self, file_id: str, count: int) -> np.ndarray:
        """Sinh int64 ID tăng dần từ file_id hash base để giải mã ngược được bằng phép trừ (vector_id - base_id - 1)"""
        base_hash = hashlib.sha256(file_id.encode("utf-8")).digest()[:8]
        base_id = int.from_bytes(base_hash, "big") & 0x7FFFFFFFFFFFFFFF
        return np.array([base_id + idx + 1 for idx in range(count)], dtype=np.int64)

    def _get_embedding_model(self, provider: EProviderName) -> str:
        for provider_record in self.config_provider.get_list_providers():
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