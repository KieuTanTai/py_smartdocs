import asyncio
import hashlib
from pathlib import Path
from typing import List, Tuple
import uuid
from venv import create
import faiss
from typing import Any
import numpy as np

# Import Interface và DTO

from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn
from backend.apps.core.interfaces.core.chunk.i_chunking import IChunking
from backend.apps.core.interfaces.core.normalize.i_normalize import INormalize
from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam, ICacheParamValue
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest, IEmbeddingResponse
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBUpsertResponse
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse, IChunkResponse
from backend.apps.core.interfaces.dataclass.tasks.i_upload_response import IDocumentResponse, IEmbedResponse, IGraphRagParam, IGraphRagUploadResponse, IUploadResponse
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import (
    INeo4jService,
)
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import (
    IConnectCacheSession,
)
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import (
    IExtractContent,
)
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import (
    ILocateService,
)
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import (
    IVectorStoreService,
)
from backend.apps.core.interfaces.services.repository.i_connect_graph_db_session import IConnectGraphDBSession
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.job.i_upload_job import IUploadJob
from backend.apps.utils.hash_content import hash_to_numpy_int64_by_str_content
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.embeddings.google_genai import GeminiEmbedder
from neo4j_graphrag.retrievers import VectorCypherRetriever
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import (
    ICompletionRequest,
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
        session_provider: IConnectGraphDBSession,
        llm_prompt_structure: ILLMPromptStructure,
    ):
        self.extract_service = extract_service
        self.normalize = normalize
        self.chunker = chunker
        self.cache_session = cache_session
        self.llm_provider_factory = llm_provider_factory
        self.locate_service = locate_service
        self.config_provider = config_provider
        self.logger = logger
        self.llm_prompt_structure = llm_prompt_structure
        self.session_provider = session_provider

    def step_extract_and_normalize(
        self, file_path: Path, provider: EProviderName, file_caller: str = ""
    ) -> IExtractResponse:
        response = self.step_extract(file_path, provider, file_caller)
        normalized_text = self.step_normalize(response.extracted_text, file_caller)
        response.extracted_text = normalized_text
        return response

    def step_extract(
        self, file_path: Path, provider: EProviderName, file_caller: str = ""
    ) -> IExtractResponse:
        response = self.extract_service.extract(
            file_path, provider
        )
        self.logger.info(
            f"Extracted text from {file_path.name} with provider {provider}, some value return: {response.extracted_text[:100]}",
            Path(__file__).name,
            file_caller,
            self.step_extract.__name__,
        )
        if not response.extracted_text:
            self.logger.error(
                f"Extracted text from {file_path.name} is empty.",
                Path(__file__).name,
                file_caller,
                self.step_extract.__name__,
            )
            raise ValueError(f"Extracted text from {file_path.name} is empty.")
        return response

    def step_normalize(self, raw_text: str, file_caller: str = "") -> str:
        self.logger.info(
            f"Normalizing text, some value return: {raw_text[:100]}",
            Path(__file__).name,
            file_caller,
            self.step_normalize.__name__,
        )
        return self.normalize.normalize(raw_text)

    def step_chunk(
        self, document_id: str, normalized_text: str, file_caller: str = ""
    ) -> IChunkResponse:
        chunk_texts = self.chunker.create_chunks(normalized_text)
        self.logger.info(
            f"Chunked text, some value return: {chunk_texts[0][:100]}, total chunks: {len(chunk_texts)}",
            Path(__file__).name,
            file_caller,
            self.step_chunk.__name__,
        )
        # * NOTE: change chunk keys to tuple[np.int64, str] to store in cache and using for ids in faiss service
        chunk_keys_tuples = self.build_chunk_keys(document_id, chunk_texts, file_caller=file_caller)

        # * NOTE: change field chunk_keys from List[str] to List[np.int64] to store the hashed keys for faiss ids, the original keys are stored in cache with the hashed keys as reference
        response = IChunkResponse(
            document_id=document_id,
            chunk_keys=[k for k, _ in chunk_keys_tuples],
            chunk_texts=chunk_texts,
        )
        self.logger.info(
            f"Chunk step completed for document {document_id} with response: {response}",
            Path(__file__).name,
            file_caller,
            self.step_chunk.__name__,
        )
        return response

    def step_embed(
        self,
        chunk_response: IChunkResponse,
        provider: EProviderName,
        file_caller: str = "",
    ) -> IEmbedResponse:
        chunk_texts = chunk_response.chunk_texts
        document_id = chunk_response.document_id
        self.logger.info(
            f"Embedding chunk texts for document {document_id} with provider {provider}",
            Path(__file__).name,
            file_caller,
            self.step_embed.__name__,
        )
        embeddings = self.__embed_chunk_texts(chunk_texts, provider)
        return IEmbedResponse(document_id, embeddings)

    def step_save(
        self,
        provider: EProviderName,
        faiss_file_id: uuid.UUID,
        document_ids: List[str],
        embedding_batches: List[np.ndarray],
        chunk_texts: List[str],
        paths: List[Path],
        ids: np.ndarray,
        file_caller: str = "",
    ) -> IUploadResponse | None:
        self.__validate_before_save(embedding_batches, ids, document_ids, paths, chunk_texts, provider, file_caller=file_caller)
        embed_stack = np.vstack(embedding_batches)
        self.logger.info(
            f"Stacked embeddings shape: {embed_stack.shape} for provider {provider}",
            Path(__file__).name,
            file_caller,
            self.step_save.__name__,
        )

        faiss_upsert_response, faiss_index = self.__save_to_faiss(
            provider, embed_stack, faiss_file_id, ids, file_caller=file_caller
        )

        bm25_response = self.__save_to_bm25(
            provider, chunk_texts, faiss_file_id, file_caller=file_caller
        )

        documents = [IDocumentResponse(document_id=doc_id, path=path) for doc_id, path in zip(document_ids, paths)]

        return IUploadResponse(
            faiss_index=faiss_index,
            faiss_file_id=faiss_file_id,
            vector_ids=ids.tolist(),
            embeddings_stack=embed_stack,
            documents=documents,
            faiss_upsert=faiss_upsert_response,
            bm25_upsert=bm25_response,
            created_at= np.datetime64("now"),
        )

    def summarize_document(self, 
                            faiss_index: faiss.IndexFlatL2 | faiss.IndexIDMap, 
                            faiss_file_id: uuid.UUID,
                            embeddings_stack: np.ndarray,
                            cache_params: List[ICacheParam],
                            provider: EProviderName,
                            model_name: str,
                            file_caller: str = "") -> str:
        faiss_service = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
        if not isinstance(faiss_service, IVectorStoreService) or faiss_service is None:
            self.logger.error(
                f"Vector store service for FAISS is not properly initialized",
                Path(__file__).name,
                self.step_embed.__name__,
            )
            raise ValueError(
                "Vector store service for FAISS is not properly initialized"
            )
        original_texts = self.__get_orriginal_texts(faiss_service, faiss_index, faiss_file_id, embeddings_stack, cache_params, file_caller)

        llm_client = self.llm_provider_factory.get_provider(provider)
        template = self.llm_prompt_structure.build_summary_prompt(original_texts)
        request = ICompletionRequest(provider, model_name, template)
        return llm_client.generate(request, file_caller=self.summarize_document.__name__)

    def step_cache(
        self,
        chunk_response: IChunkResponse,
        embedding_response: IEmbedResponse,
        file_caller: str = "",
    ) -> IChunkAndCacheResponse:
        self.logger.info(
            f"Creating cache for document {chunk_response.document_id}",
            Path(__file__).name,
            file_caller,
            self.step_cache.__name__,
        )
        try:
            cache_service = self.cache_session.connect(
                file_caller=self.step_cache.__name__
            )
            if not isinstance(cache_service, ICacheService):
                raise ValueError("Cache service is not properly initialized")
            # * NOTE: convert chunk and embedding responses to ICacheParamValue list to store in cache, because cache only accept string key and ICacheParamValue list as value, the original chunk keys are stored in cache with the hashed keys as reference, so when get from cache, we can use the hashed keys to get the original chunk keys and chunk texts for further processing
            cache_param = ICacheParam(
                key=chunk_response.document_id,
                values=self.__convert_to_cache_param_value(chunk_response, embedding_response),
            )
            path = cache_service.set(
                cache_param, file_caller=self.step_cache.__name__
            )
            if path is None:
                self.logger.error(
                    f"Failed to cache chunked data for document {chunk_response.document_id}",
                    Path(__file__).name,
                    file_caller,
                    self.step_cache.__name__,
                )
                raise ValueError(
                    f"Failed to cache chunked data for document {chunk_response.document_id}"
                )
            self.logger.info(
                f"Chunked data cached for document {chunk_response.document_id} at '{path}'",
                Path(__file__).name,
                file_caller,
                self.step_cache.__name__,
            )
        finally:
            self.logger.info(
                f"Disconnecting cache session for document {chunk_response.document_id}",
                Path(__file__).name,
                file_caller,
                self.step_cache.__name__,
            )
            self.cache_session.disconnect(
                file_caller=self.step_cache.__name__
            )
        return IChunkAndCacheResponse(chunk_response, cache_param, path)

    async def step_build_knowledge_graph(
        self,
        conversation_id: uuid.UUID,
        graph_params: List[IGraphRagParam],
        model_name: str,
        embedding_model_name: str,
        provider: EProviderName = EProviderName.GEMINI,
        similarity_fn: ESimilarityFn = ESimilarityFn.COSINE,
        file_caller: str = "",
    ) -> IGraphRagUploadResponse:
        self.logger.info(
            f"Create a knowledge graph for the given documents {', '.join([graph_param.document_id for graph_param in graph_params])}",
            Path(__file__).name,
            file_caller,
            self.step_build_knowledge_graph.__name__,
        )

        provider_client = self.llm_provider_factory.get_provider(provider)
        llm_model = provider_client.get_llm_model(model_name, file_caller)
        embedder = provider_client.get_embedder_model(embedding_model_name, file_caller)
        template = self.llm_prompt_structure.build_prompt_for_retrieval_query()
        retriever = await self.__run_pipeline_create_retriever(
            conversation_id=conversation_id,
            embedder=embedder,
            llm_model=llm_model,
            template=template,
            params=graph_params,
            similarity_fn=similarity_fn,
            file_caller=file_caller,
        )
        return IGraphRagUploadResponse(
            conversation_id=conversation_id,
            list_document_ids=[param.document_id for param in graph_params],
            graph_param_list=graph_params,
            graph_retriever=retriever,
            created_at=np.datetime64("now"),
        )

    def build_chunk_keys(
        self, file_id: str, chunk_texts: List[str], file_caller: str = ""
    ) -> List[Tuple[np.int64, str]]:
        """create chunk keys based on file_id with structure: file_id:chunk_index
        after that hashing this key to 64 bit integer for numpy array dtype int64
        """
        chunk_keys_tuples = []
        for idx, chunk in enumerate(chunk_texts):
            chunk_key_str = f"{file_id}:{idx}"
            chunk_key_hash = hash_to_numpy_int64_by_str_content(chunk_key_str)
            chunk_keys_tuples.append((chunk_key_hash, chunk))
        if not chunk_keys_tuples:
            self.logger.error(
                f"Failed to build chunk keys for file_id {file_id} because chunk_keys_tuples is empty",
                Path(__file__).name,
                file_caller,
                self.build_chunk_keys.__name__,
            )
            raise ValueError(
                f"Failed to build chunk keys for file_id {file_id} because chunk_keys_tuples is empty"
            )
        self.logger.info(
            f"Built chunk keys for file_id {file_id} with chunk keys: {[k for k, _ in chunk_keys_tuples]}",
            Path(__file__).name,
            file_caller,
            self.build_chunk_keys.__name__,
        )
        return chunk_keys_tuples

    def build_name(
        self, document_ids: List[str], split_by: str = "_", file_caller: str = ""
    ) -> str:
        sorted_ids = sorted(document_ids)
        name = split_by.join(sorted_ids)
        self.logger.info(
            f"Built file name '{name}' from document IDs: {document_ids}",
            Path(__file__).name,
            file_caller,
            self.build_name.__name__,
        )
        return name

    ## ------------------- PRIVATE METHODS -------------------
    async def __run_pipeline_create_retriever(
        self,
        conversation_id: uuid.UUID,
        embedder: Embedder,
        llm_model: LLMInterface,
        template: str,
        params: List[IGraphRagParam],
        similarity_fn: ESimilarityFn,
        file_caller: str = "",
    ) -> VectorCypherRetriever:
        try:
            service = self.session_provider.connect(file_caller=self.step_build_knowledge_graph.__name__)
            if (service is None) or (not isinstance(service, INeo4jService)):
                raise ValueError("Failed to get a valid Neo4jService instance from the session")
            service.create_vector_index(
                index_name=conversation_id, 
                dimension=embedder.embedding_dim if isinstance(embedder, GeminiEmbedder) else 768,
                label="Chunk",
                embedding_property="embedding",
                similarity_fn=similarity_fn,
            )

            retriever = await service.execute_file_to_kg_pipeline(
                retrieval_query=template,
                index_name=conversation_id,
                params=params,
                llm_model=llm_model,
                embedder=embedder,
                file_caller=file_caller,
            )
            return retriever
        except Exception as e:
            self.logger.error(
                f"Failed to create vector index for document {conversation_id} with error: {str(e)}",
                Path(__file__).name,
                file_caller,
                self.step_build_knowledge_graph.__name__,
            )
            raise e
        finally:
            self.session_provider.disconnect(file_caller=self.step_build_knowledge_graph.__name__)

    def __validate_before_save(self, embedding_batches: List[np.ndarray], ids: np.ndarray, document_ids: List[str], chunk_paths: List[Path], chunk_texts: List[str], provider: EProviderName, file_caller: str = "") -> None:
        if embedding_batches is None or len(embedding_batches) == 0:
            self.logger.error(
                f"No embeddings to save for provider {provider} for document ids: {document_ids}",
                Path(__file__).name,
                file_caller,
                self.step_save.__name__,
            )
            raise ValueError(
                f"No embeddings to save for provider {provider} for document ids: {document_ids}"
            )

        if chunk_texts is None or len(chunk_texts) == 0:
            self.logger.error(
                f"No chunk texts to save for provider {provider} for document ids: {document_ids}",
                Path(__file__).name,
                file_caller,
                self.step_save.__name__,
            )
            raise ValueError(
                f"No chunk texts to save for provider {provider} for document ids: {document_ids}"
            )

        if chunk_paths is None or len(chunk_paths) == 0:
            self.logger.error(
                f"No chunk paths provided for provider {provider} for document ids: {document_ids}",
                Path(__file__).name,
                file_caller,
                self.step_save.__name__,
            )
            raise ValueError(
                f"No chunk paths provided for provider {provider} for document ids: {document_ids}"
            )        

        if len(chunk_paths) != len(document_ids):
            self.logger.error(
                f"Length of chunk paths {len(chunk_paths)} does not match length of document ids {len(document_ids)} for provider {provider} and document ids: {document_ids}",
                Path(__file__).name,
                file_caller,
                self.step_save.__name__,
            )
            raise ValueError(
                f"Length of chunk paths {len(chunk_paths)} does not match length of document ids {len(document_ids)} for provider {provider} and document ids: {document_ids}"
            )

        if len(chunk_texts) != len(ids):
            self.logger.error(
                f"Length of chunk texts {len(chunk_texts)} does not match length of ids {len(ids)} for provider {provider} for document ids: {document_ids}",
                Path(__file__).name,
                file_caller,
                self.step_save.__name__,
            )
            raise ValueError(
                f"Length of chunk texts {len(chunk_texts)} does not match length of ids {len(ids)} for provider {provider} for document ids: {document_ids}"
            )

    def __save_to_faiss(
        self,
        provider: EProviderName,
        embed_stack: np.ndarray,
        file_name: uuid.UUID,
        ids: np.ndarray = np.ndarray([], dtype=np.int64),
        file_caller: str = "",
    ) -> tuple[IVectorDBUpsertResponse, faiss.IndexFlatL2 | faiss.IndexIDMap]:
        self.logger.info(
            f"Saving embeddings to FAISS for provider {provider} with ids: {ids}",
            Path(__file__).name,
            file_caller,
            self.__save_to_faiss.__name__,
        )
        vector_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)

        if not isinstance(vector_store, IVectorStoreService) or vector_store is None:
            self.logger.error(
                f"Vector store service for FAISS is not properly initialized",
                Path(__file__).name,
                file_caller,
                self.__save_to_faiss.__name__,
            )
            raise ValueError(
                "Vector store service for FAISS is not properly initialized"
            )

        index = vector_store.create_index(
            embed_stack, ids, file_caller=self.__save_to_faiss.__name__
        )
        faiss_file_name = vector_store.upsert(
            index, file_name, file_caller=self.__save_to_faiss.__name__
        )
        self.logger.info(
            f"Saved embeddings to FAISS with:\n    file name: {faiss_file_name}\n    index: {index}\n    file name: {file_name}\n    provider: {provider}",
            Path(__file__).name,
            file_caller,
            self.__save_to_faiss.__name__,
        )
        upsert_response = vector_store.upsert(
            index, file_name, file_caller=self.__save_to_faiss.__name__
        )
        return upsert_response, index

    def __save_to_bm25(
        self,
        provider: EProviderName,
        chunk_texts: List[str],
        file_name: uuid.UUID,
        file_caller: str = "",
    ) -> IVectorDBUpsertResponse | None:
        if chunk_texts is None or len(chunk_texts) == 0:
            self.logger.warning(
                f"No chunk texts to save to BM25 for provider {provider} with file name: {file_name}",
                Path(__file__).name,
                file_caller,
                self.__save_to_bm25.__name__,
            )
            return None
        self.logger.info(
            f"Saving chunk texts to BM25 for provider {provider} with file name: {file_name}",
            Path(__file__).name,
            file_caller,
            self.__save_to_bm25.__name__,
        )
        vector_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)

        if not isinstance(vector_store, IVectorStoreService) or vector_store is None:
            self.logger.error(
                f"Vector store service for BM25 is not properly initialized",
                Path(__file__).name,
                file_caller,
                self.__save_to_bm25.__name__,
            )
            raise ValueError(
                "Vector store service for BM25 is not properly initialized"
            )

        upsert_response = vector_store.upsert(
            chunk_texts, file_name, file_caller=self.__save_to_bm25.__name__
        )
        self.logger.info(
            f"Saved chunk texts to BM25 with:\n    id: {upsert_response.id}\n    file name: {file_name}\n    provider: {provider}",
            Path(__file__).name,
            file_caller,
            self.__save_to_bm25.__name__,
        )
        return upsert_response

    def __convert_to_cache_param_value(
        self, chunk_response: IChunkResponse, embedding_response: IEmbedResponse
    ) -> List[ICacheParamValue]:
        """Convert chunk and embedding responses to list of ICacheParamValue"""
        return [
            ICacheParamValue(index=chunk_key, text_value=chunk_text, embedding=embedding)
            for chunk_key, chunk_text, embedding in zip(chunk_response.chunk_keys, chunk_response.chunk_texts, embedding_response.embeddings.tolist())
        ]

    def __get_orriginal_texts(
        self,
        faiss_service: IVectorStoreService,
        faiss_index: faiss.IndexFlatL2 | faiss.IndexIDMap,
        faiss_file_id: uuid.UUID,
        embeddings_stack: np.ndarray,
        cache_params: List[ICacheParam],
        file_caller: str = "",
    ) -> str:
        response = faiss_service.search(
            faiss_index,
            faiss_file_id,
            embeddings_stack,
            limit=5,
            file_caller=self.summarize_document.__name__,
        )
        indices = response.indices
        rows_by_id = {
            int(value.index): value for param in cache_params for value in param.values
        }

        filtered_cache_values = [
            rows_by_id[int(index)] for index in indices if int(index) in rows_by_id
        ]

        original_texts = [value.text_value for value in filtered_cache_values]
        self.logger.info(
            "Retrieved original texts for summarization: {}".format(
                original_texts[:100]
            ),
            Path(__file__).name,
            file_caller,
            self.summarize_document.__name__,
        )
        return "\n".join(original_texts)

    #! NOTE: ids build by hashing the content to ensure the same content, not by file_id, will have the same id, which is important for deduplication and update scenarios. The hash is truncated to fit within typical ID length limits while minimizing collision risk.
    def __get_embedding_model(self, provider: EProviderName) -> str:
        for provider_record in self.config_provider.get_list_providers():
            if provider_record.provider_name == provider:
                return provider_record.embed_model_name
        raise ValueError(f"Embedding model not configured for provider {provider}")

    def __embed_chunk_texts(
        self, chunk_texts: List[str], provider: EProviderName
    ) -> np.ndarray:
        llm_client = self.llm_provider_factory.get_provider(provider)
        model_name = self.__get_embedding_model(provider)
        list_embeddings = []
        for chunk in chunk_texts:
            embedding = llm_client.embedding(
                ICompletionRequest(provider, model_name, chunk),
                file_caller=self.__embed_chunk_texts.__name__,
            )
            list_embeddings.append(embedding.embedding)
        return np.array(list_embeddings, dtype=np.float32)
