import asyncio
import hashlib
from pathlib import Path
from typing import List, Tuple
from venv import create
import faiss
from typing import Any
import numpy as np

# Import Interface và DTO

from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.chunk.i_chunking import IChunking
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.core.normalize.i_normalize import INormalize
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBUpsertResponse
from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam, ICacheParamValue, ICacheParamValue
from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import INeo4jService
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import IExtractContent
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse
from backend.apps.core.interfaces.dataclass.tasks.i_embed_and_save_response import IEmbedResponse, ISaveResponse
from backend.apps.interfaces.job.i_upload_job import IUploadJob
from backend.apps.utils.hash_content import hash_to_numpy_int64_by_str_content, sha256_embedded_content, sha256_embedded_contents
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import (
    ICompletionRequest,
    IEmbeddingResponse,
)

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
        neo4j_service: INeo4jService,
        llm_prompt_structure: ILLMPromptStructure
    ):
        self.extract_service = extract_service
        self.normalize = normalize
        self.chunker = chunker
        self.cache_session = cache_session
        self.llm_provider_factory = llm_provider_factory
        self.locate_service = locate_service
        self.config_provider = config_provider
        self.logger = logger
        self.neo4j_service = neo4j_service
        self.llm_prompt_structure = llm_prompt_structure

    def step_extract(self, file_paths: List[Path], provider: EProviderName, file_caller: str = "") -> str:
        extracted_texts = []
        for path in file_paths:
            response = self.extract_service.extract(path, provider) #type IExtractResponse {document_id: str, extracted_text: str, model: str, pages_processed: int, doc_size_bytes: OptionalNullable[int] = UNSET (from mistralai.client.types)}
            if not response.extracted_text:
                self.logger.warning(f"Extracted text from {path.name} is empty.", Path(__file__).name, file_caller, self.step_extract.__name__)
                continue
            
            text_str = response.extracted_text
            extracted_texts.append(text_str)
            self.logger.info(f"Extracted text from {path.name}, length: {len(text_str)}", Path(__file__).name, file_caller, self.step_extract.__name__)
        
        if not extracted_texts:
            raise ValueError(f"All extracted texts from {len(file_paths)} files are empty.")
            
        return extracted_texts

    def step_normalize(self, raw_text: List[str], file_caller: str = "") -> str:
        normalized_text = []
        for raw in raw_text:
            normalized = self.normalize.normalize(raw)
            normalized_text.append(normalized)
        
        self.logger.info(f"Normalized {len(normalized_text)} texts.", Path(__file__).name, file_caller, self.step_normalize.__name__)
        return normalized_text

    def step_chunk_and_cache(self, document_id: str, normalized_text: List[str], file_caller: str = "") -> IChunkAndCacheResponse:
        combined_text = "\n\n".join(normalized_text)
        
        chunk_texts = self.chunker.create_chunks(combined_text)
        self.logger.info(f"Chunked combined text into {len(chunk_texts)} chunks", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)        # * NOTE: change chunk keys to tuple[np.int64, str] to store in cache and using for ids in faiss service
        
        chunk_keys_tuples = self.__build_chunk_keys(document_id, chunk_texts)
        path_cache = self.__cache_chunk_data(document_id, chunk_keys_tuples, file_caller=file_caller)

        # * NOTE: change field chunk_keys from List[str] to List[np.int64] to store the hashed keys for faiss ids, the original keys are stored in cache with the hashed keys as reference
        response = IChunkAndCacheResponse(
            document_id=document_id,
            chunk_keys=[k for k, _ in chunk_keys_tuples],
            chunk_texts=chunk_texts,
            path=path_cache
        )
        self.logger.info(f"Chunk and cache step completed for document {document_id} with response: {response}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
        return response

    def step_embed(self, chunk_and_cache_response: IChunkAndCacheResponse, provider: EProviderName, file_caller: str = "") -> IEmbedResponse:
        chunk_texts = chunk_and_cache_response.chunk_texts
        document_id = chunk_and_cache_response.document_id
        self.logger.info(f"Embedding chunk texts for document {document_id} with provider {provider}", Path(__file__).name, file_caller, self.step_embed.__name__)
        embeddings = self.__embed_chunk_texts(chunk_texts, provider)
        return IEmbedResponse(document_id=document_id, embeded_metadata=embeddings)

    def step_save(self, provider: EProviderName, document_ids: List[str], embed_responses: List[np.ndarray], chunk_texts: List[str] = [], ids: np.ndarray = np.ndarray([], dtype=np.int64), file_caller: str = "") -> ISaveResponse:
        faiss_file_name = self.__build_file_name(document_ids, file_caller=file_caller)
        embed_stack = np.vstack([np.array(embed, dtype=np.float32) for embed in embed_responses])
        self.logger.info(f"Stacked embeddings shape: {embed_stack.shape} for provider {provider}", Path(__file__).name, file_caller, self.step_save.__name__)
        faiss_upsert_response, faiss_index = self.__save_to_faiss(provider, embed_stack, faiss_file_name, ids, file_caller=file_caller)

        bm25_response = self.__save_to_bm25(provider, chunk_texts, faiss_file_name, file_caller=file_caller)
        return ISaveResponse(faiss_index=faiss_index, faiss_file_name=faiss_file_name, vector_ids=ids.tolist(), faiss_upsert=faiss_upsert_response, bm25_upsert=bm25_response, crate_at=faiss_upsert_response.create_at)

    def step_build_knowledge_graph(self, document_id: str, extracted_text: str, provider = EProviderName, file_caller: str = ""):
        """Bước kích hoạt Neo4j chạy ngầm để bóc tách thực thể từ văn bản"""
        self.logger.info(f"Khởi tạo Graph RAG cho tài liệu {document_id}", Path(__file__).name, file_caller, self.step_build_knowledge_graph.__name__)
        index_name = f"graph_index_{document_id}"
        try:
            self.neo4j_service.create_vector_index(index_name=index_name, dimension=768, label="Chunk")
        except Exception as e:
            self.logger.error(f"Failed to create vector index for document {document_id} with error: {str(e)}", Path(__file__).name, file_caller, self.step_build_knowledge_graph.__name__)
        
        llm_client = self.llm_provider_factory.get_provider(provider)
        embedder = self.__embed_chunk_texts([extracted_text], provider)

        asyncio.run(self._run_kg_pipeline_async(
            index_name=index_name,
            extracted_text=extracted_text,
            llm_client=llm_client,
            embedder=embedder,
            file_caller=file_caller
        ))
        
        self.logger.info(f"Đã xây dựng xong Knowledge Graph cho {document_id}")
    
    async def _run_kg_pipeline_async(self, index_name: str, extracted_text: str, llm_client, embedder, file_caller: str):
        """Hàm bất đồng bộ chạy ngầm để đẩy Text vào Neo4j Pipeline"""
        # Lưu ý: Tuỳ thuộc vào bạn đang dùng tên hàm 'execute_file...' hay 'execute_text...' ở file interface nhé
        await self.neo4j_service.execute_file_to_kg_pipeline(
            retrieval_query="MATCH (c:Chunk)-[:MENTIONS]->(e:Entity) RETURN c.text AS text, e.id AS entity",
            index_name=index_name,
            extracted_texts=[extracted_text],
            llm_model=llm_client,
            embedder=embedder,
            file_caller=file_caller
        )

    ## ------------------- PRIVATE METHODS -------------------

    def __save_to_faiss(self, provider: EProviderName, embed_stack: np.ndarray, file_name: str, ids: np.ndarray = np.ndarray([], dtype=np.int64), file_caller: str = "") -> tuple[IVectorDBUpsertResponse, faiss.IndexFlatL2 | faiss.IndexIDMap]:
        self.logger.info(f"Saving embeddings to FAISS for provider {provider} with ids: {ids}", Path(__file__).name, file_caller, self.__save_to_faiss.__name__)
        vector_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)

        if not isinstance(vector_store, IVectorStoreService) or vector_store is None:
            self.logger.error(f"Vector store service for FAISS is not properly initialized", Path(__file__).name, file_caller, self.__save_to_faiss.__name__)
            raise ValueError("Vector store service for FAISS is not properly initialized")

        index = vector_store.create_index(embed_stack, ids, file_caller=self.__save_to_faiss.__name__)
        faiss_file_name = vector_store.upsert(index, file_name, file_caller=self.__save_to_faiss.__name__)
        self.logger.info(f"Saved embeddings to FAISS with:\n    file name: {faiss_file_name}\n    index: {index}\n    file name: {file_name}\n    provider: {provider}", 
                         Path(__file__).name, file_caller, self.__save_to_faiss.__name__)
        upsert_response = vector_store.upsert(index, file_name, file_caller=self.__save_to_faiss.__name__)
        return  upsert_response, index

    def __save_to_bm25(self, provider: EProviderName, chunk_texts: List[str], file_name: str, file_caller: str = "") -> IVectorDBUpsertResponse | None:
        if chunk_texts is None or len(chunk_texts) == 0:
            self.logger.warning(f"No chunk texts to save to BM25 for provider {provider} with file name: {file_name}", Path(__file__).name, file_caller, self.__save_to_bm25.__name__)
            return None
        self.logger.info(f"Saving chunk texts to BM25 for provider {provider} with file name: {file_name}", Path(__file__).name, file_caller, self.__save_to_bm25.__name__)
        vector_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)

        if not isinstance(vector_store, IVectorStoreService) or vector_store is None:
            self.logger.error(f"Vector store service for BM25 is not properly initialized", Path(__file__).name, file_caller, self.__save_to_bm25.__name__)
            raise ValueError("Vector store service for BM25 is not properly initialized")

        upsert_response = vector_store.upsert(chunk_texts, file_name, file_caller=self.__save_to_bm25.__name__)
        self.logger.info(f"Saved chunk texts to BM25 with:\n    id: {upsert_response.id}\n    file name: {file_name}\n    provider: {provider}", 
                         Path(__file__).name, file_caller, self.__save_to_bm25.__name__)
        return upsert_response

    def __cache_chunk_data(self, document_id: str, chunk_keys_tuples: List[Tuple[np.int64, str]], file_caller: str = "") -> Path:
        self.logger.info(f"Creating cache for document {document_id}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
        try:
            cache_service = self.cache_session.connect(file_caller=self.step_chunk_and_cache.__name__)
            if not isinstance(cache_service, ICacheService):
                raise ValueError("Cache service is not properly initialized")
            # * NOTE: convert chunk_keys_tuples to ICacheParamValue list to store in cache, because cache only accept string key and ICacheParamValue list as value, the original chunk keys are stored in cache with the hashed keys as reference, so when get from cache, we can use the hashed keys to get the original chunk keys and chunk texts for further processing
            cache_params = ICacheParam(key=document_id, values=self.__convert_to_cache_param_value(chunk_keys_tuples))
            path = cache_service.set(cache_params, file_caller=self.step_chunk_and_cache.__name__)
            if path is None:
                self.logger.error(f"Failed to cache chunked data for document {document_id}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
                raise ValueError(f"Failed to cache chunked data for document {document_id}")
            self.logger.info(f"Chunked data cached for document {document_id} at '{path}'", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
        finally:
            self.logger.info(f"Disconnecting cache session for document {document_id}", Path(__file__).name, file_caller, self.step_chunk_and_cache.__name__)
            self.cache_session.disconnect(file_caller=self.step_chunk_and_cache.__name__)
        return path

    def __build_file_name(self, document_ids: List[str], file_caller: str = "") -> str:
        name = "_".join(document_ids)
        self.logger.info(f"Built file name '{name}' from document IDs: {document_ids}", Path(__file__).name, file_caller, self.__build_file_name.__name__)
        return name


    def __convert_to_cache_param_value(self, chunk_keys_tuples: List[Tuple[np.int64, str]]) -> List[ICacheParamValue]:
        """Convert list of tuples (chunk_key, chunk_text) to list of ICacheParamValue"""
        return [ICacheParamValue(index=chunk_key, text_value=chunk_text) for chunk_key, chunk_text in chunk_keys_tuples]

    def __convert_list_int64_to_np_array(self, list_int64: List[np.int64]) -> np.ndarray:
        """Convert a list of np.int64 to a numpy array of dtype int64."""
        return np.array(list_int64, dtype=np.int64)

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
    def __get_embedding_model(self, provider: EProviderName) -> str:
        for provider_record in self.config_provider.get_list_providers():
            if provider_record.provider_name == provider:
                return provider_record.embed_model_name
        raise ValueError(f"Embedding model not configured for provider {provider}")

    def __embed_chunk_texts(self, chunk_texts: List[str], provider: EProviderName) -> List[IEmbeddingResponse]:
        llm_client = self.llm_provider_factory.get_provider(provider)
        model_name = self.__get_embedding_model(provider)
        list_embeddings: list[IEmbeddingResponse] = []
        for chunk in chunk_texts:
            embedding = llm_client.embedding(
                ICompletionRequest(provider, model_name, chunk),
                file_caller=self.__embed_chunk_texts.__name__,
            )
            list_embeddings.append(embedding)
        return list_embeddings
    

