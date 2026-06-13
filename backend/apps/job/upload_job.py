import hashlib
from pathlib import Path
from typing import List, Tuple
from venv import create
import numpy as np

# Import Interface và DTO

from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.chunk.i_chunking import IChunking
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.core.normalize.i_normalize import INormalize
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.response.i_vector_db_response import IVectorDBUpsertResponse
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import IExtractContent
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse
from backend.apps.core.interfaces.tasks.i_embed_and_save_response import IEmbedAndSaveResponse
from backend.apps.interfaces.job.i_upload_job import IUploadJob
from backend.apps.utils.hash_content import hash_to_numpy_int64_by_str_content, sha256_embedded_content, sha256_embedded_contents


class UploadJob(IUploadJob):
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

    def step_extract(self, file_path: Path, provider: EProviderName, file_caller: str = "") -> str:
        extracted_text = self.extract_service.extract_from_file_text(file_path, provider)
        self.logger.info(f"Extracted text from {file_path.name} with provider {provider}, some value return: {extracted_text[0][:100]}", Path(__file__).name, file_caller, self.step_extract.__name__)
        if not extracted_text:
            self.logger.error(f"Extracted text from {file_path.name} is empty.", Path(__file__).name, file_caller, self.step_extract.__name__)
            raise ValueError(f"Extracted text from {file_path.name} is empty.")
        return extracted_text

    def step_normalize(self, raw_text: str, file_caller: str = "") -> str:
        self.logger.info(f"Normalizing text, some value return: {raw_text[:100]}", Path(__file__).name, file_caller, self.step_normalize.__name__)
        return self.normalize.normalize(raw_text)

    def step_chunk_and_cache(self, document_id: str, normalized_text: str, file_caller: str = "") -> IChunkAndCacheResponse:
        chunk_texts = self.chunker.create_chunks(normalized_text)
        self.logger.info(f"Chunked text, some value return: {chunk_texts[0][:100]}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
        #* NOTE: change chunk keys to tuple[np.int64, str] to store in cache and using for ids in faiss service
        chunk_keys_tuples = self.__build_chunk_keys(document_id, chunk_texts)
        path_cache = self.__cache_chunk_data(document_id, chunk_keys_tuples, file_caller=file_caller)

        #* NOTE: change field chunk_keys from List[str] to List[np.int64] to store the hashed keys for faiss ids, the original keys are stored in cache with the hashed keys as reference
        response = IChunkAndCacheResponse(
            document_id=document_id,
            chunk_keys=[k for k, _ in chunk_keys_tuples],
            chunk_texts=chunk_texts,
            path=path_cache
        )
        self.logger.info(f"Chunk and cache step completed for document {document_id} with response: {response}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
        return response

    #! NOTE: not need document  id here, just chunk_texts is enough, but chunk_data must be type List[List[str]]
    #! because np.vstack use for stack embeddings of multiple files, chunk_data now just have one file, but in the future may have multiple files, 
    #! so we need to keep the type consistent to avoid refactor in the future when support multiple files.
    #! I don't fix that yet, give this problems for author fix :))
    def step_embed_and_save(self, chunk_data: IChunkAndCacheResponse, provider: EProviderName, file_caller: str = "") -> IEmbedAndSaveResponse:
        document_id = chunk_data.document_id
        chunk_keys = chunk_data.chunk_keys
        chunk_texts = chunk_data.chunk_texts

        embeddings = self.__embed_chunk_texts(chunk_texts, provider)
        vectors = np.vstack(embeddings)
        #! NOTE: ids build by hashing

        faiss_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
        if isinstance(faiss_store, IVectorStoreService):
            faiss_index = faiss_store.create_index(vectors, vector_ids, file_caller=self.step_embed_and_save.__name__)
            faiss_upsert = faiss_store.upsert(faiss_index, vector_id=document_id, file_caller=self.step_embed_and_save.__name__)
        else:
            raise ValueError("FAISS store is not properly initialized")

        bm25_texts_map = {str(k): v for k, v in zip(chunk_keys, chunk_texts)}
        bm25_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)
        if isinstance(bm25_store, IVectorStoreService):
            bm25_upsert = bm25_store.upsert(bm25_texts_map, vector_id=document_id, file_caller=self.step_embed_and_save.__name__)
        else:
            raise ValueError("BM25 store is not properly initialized")

        file_key = sha256_embedded_content(vectors)

        #! NOTE: this must build for multiple files, so dont_use document_id on response, 
        #! so, you can use faiss_upsert.id where this id is plus from document_ids split by '_'
        return IEmbedAndSaveResponse(
            document_id=document_id,
            file_key=file_key,
            vector_ids=faiss_upsert.id,
            faiss_upsert=IVectorDBUpsertResponse(id=faiss_upsert.id, create_at=faiss_upsert.create_at, sumarize_content=faiss_upsert.sumarize_content, is_success=faiss_upsert.is_success),
            bm25_upsert=IVectorDBUpsertResponse(id=bm25_upsert.id, create_at=bm25_upsert.create_at, sumarize_content=bm25_upsert.sumarize_content, is_success=bm25_upsert.is_success)
        )


    def __cache_chunk_data(self, document_id: str, chunk_keys_tuples: List[Tuple[np.int64, str]], file_caller: str = "") -> Path:
        self.logger.info(f"Creating cache for document {document_id}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
        try:
            cache_service = self.cache_session.connect(file_caller=self.step_chunk_and_cache.__name__)
            path = cache_service.set(document_id, chunk_keys_tuples, file_caller=self.step_chunk_and_cache.__name__)
            if path is None:
                self.logger.error(f"Failed to cache chunked data for document {document_id}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
                raise ValueError(f"Failed to cache chunked data for document {document_id}")
            self.logger.info(f"Chunked data cached for document {document_id} at '{path}'", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
        finally:
            self.logger.info(f"Disconnecting cache session for document {document_id}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
            self.cache_session.disconnect(file_caller=self.step_chunk_and_cache.__name__)
        return path

    def __build_chunk_keys(self, file_id: str, chunk_texts: List[str]) -> List[Tuple[np.int64, str]]:
        """create chunk keys based on file_id with structure: file_id:chunk_index
            after that hashing this key to 64 bit integer for numpy array dtype int64
        """
        chunk_keys_tuples = []
        for idx, chunk in enumerate(chunk_texts):
            chunk_key_str = f"{file_id}:{idx}"
            chunk_key_hash = hash_to_numpy_int64_by_str_content(chunk_key_str)
            chunk_keys_tuples.append((chunk_key_hash, chunk))
        return chunk_keys_tuples
        

#! NOTE: ids build by hashing the content to ensure the same content, not by file_id, will have the same id, which is important for deduplication and update scenarios. The hash is truncated to fit within typical ID length limits while minimizing collision risk.
    # def __build_vector_ids(self, file_id: str, count: int) -> np.ndarray:
    #     """create vector ids based on file_id with structure: file_id:chunk_index, ensure the same file_id will have the same vector ids for the same number of chunks"""
    #     base_hash = hashlib.sha256(file_id.encode("utf-8")).digest()[:8]
    #     base_id = int.from_bytes(base_hash, "big") & 0x7FFFFFFFFFFFFFFF
    #     return np.array([base_id + idx + 1 for idx in range(count)], dtype=np.int64)

    def __get_embedding_model(self, provider: EProviderName) -> str:
        for provider_record in self.config_provider.get_list_providers():
            if provider_record.provider_name == provider:
                return provider_record.embed_model_name
        raise ValueError(f"Embedding model not configured for provider {provider}")

    def __embed_chunk_texts(self, chunk_texts: List[str], provider: EProviderName) -> List[np.ndarray]:
        llm_client = self.llm_provider_factory.get_provider(provider)
        model_name = self.__get_embedding_model(provider)
        embeddings = []
        for text in chunk_texts:
            response = llm_client.embedding(
                ICompletionRequest(provider=provider, model=model_name, prompt=text)
            )
            embeddings.append(response.embedding.astype(np.float32))
        return embeddings