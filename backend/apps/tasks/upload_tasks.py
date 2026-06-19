"""
Upload tasks module.
Handles the execution flow for uploaded files via background workers.
"""

from dataclasses import asdict
from typing import Any, Dict, List, Tuple, cast
from pathlib import Path
import uuid
from celery import Task
import numpy as np

from backend.apps.core.enums.e_document_status import EDocumentStatus
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse, IChunkResponse
from backend.apps.core.interfaces.services.cache.i_faiss_memory_pool import IFaissMemoryPool
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.dataclass.tasks.i_embed_and_save_response import IEmbedResponse, IExtractMapping, IGraphRagUploadResponse, IUploadResponse
from backend.apps.services.chat.models import DocumentModel
from backend.apps.interfaces.tasks.i_upload_task import IUploadTask
from backend.apps.interfaces.job.i_upload_job import IUploadJob
from neo4j_graphrag.retrievers import VectorCypherRetriever

class UploadTask(Task, IUploadTask):

    def __init__(self, upload_job: IUploadJob, logger: ILogger, faiss_memory_pool: IFaissMemoryPool, database_provider: IDatabaseProvider):
        self.upload_job = upload_job
        self.logger = logger
        self.faiss_memory_pool = faiss_memory_pool
        self.database_provider = database_provider
        self.document_database = cast(IDocumentDatabase, self.database_provider.get_model_service(DocumentModel))

    # --- MAIN ENTRY POINT ---
    @property
    def name(self) -> str:
        """Return the task name for routing."""
        self.logger.info(f"Retrieving task name for routing", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.name)
        return Path(__file__).stem  # Dynamic name based on filename

    # * New run method to handle for new interface with file paths,
    # * this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
    def run_with_paths(self, file_paths: list[Path], provider_name: EProviderName, model_name: str, file_caller: str = "") -> IUploadResponse:
        self.logger.info(f"Starting UploadTask with file paths {file_paths} and provider {provider_name} called by {file_caller}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
        try:
            # Chạy luồng lõi
            result_dataclass = self.__execute_base_pipeline_with_paths(file_paths, provider_name, model_name)
            # Lưu index vào memory pool
            self.logger.info(f"Adding FAISS index to memory pool with file ID {result_dataclass.faiss_file_id} for file paths {file_paths}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
            self.faiss_memory_pool.add_to_pool(result_dataclass.faiss_file_id, result_dataclass.faiss_index, file_caller)
            self.logger.info(f"Successfully completed UploadTask for file paths {file_paths} and provider {provider_name}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
            return result_dataclass
        except Exception as exc:
            self.logger.error(f"Error processing file paths {file_paths}: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
            raise exc

    def run_graph_pipeline_with_paths(self, file_paths: list[Path], provider_name: EProviderName, embed_model_name: str, model_name: str, file_caller: str = "") -> IGraphRagUploadResponse:
        self.logger.info(f"Starting Graph RAG UploadTask with file paths {file_paths} and provider {provider_name} called by {file_caller}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_graph_pipeline_with_paths.__name__)
        try:
            responses = self.__execute_pipeline_create_retriever_with_paths(file_paths, provider_name, model_name, embed_model_name)
            self.logger.info(f"Successfully completed Graph RAG UploadTask for file paths {file_paths} and provider {provider_name}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_graph_pipeline_with_paths.__name__)
            return responses
        except Exception as exc:
            self.logger.error(f"Error processing file paths {file_paths} for graph pipeline: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_graph_pipeline_with_paths.__name__)
            raise exc

    # --- SINGLE RESPONSIBILITY METHODS ---
    def __ensure_document_database_exists(self) -> None:
        """Ensure the document database service is available."""
        if self.document_database is None:
            self.logger.error(
                "Document database service is not available",
                source=Path(__file__).name,
                call_by=Path(__file__).name,
                method_call=self.__ensure_document_database_exists.__name__,
            )
            raise ValueError("Document database service is not available")

    def __create_document_model(self, file_path: Path | None = None, content: str | None = None) -> DocumentModel:
        """Create a new document model and set its status."""
        self.__ensure_document_database_exists()
        response = self.document_database.create_document(
            file_path=file_path,
            status=EDocumentStatus.PROCESSING,
            content=content,
            is_active=True,
        )
        return response

    def __update_document_status_and_path(self, document_id: Any, status: EDocumentStatus, file_path: Path | None = None) -> DocumentModel:
        """Update the document status and optionally its file path."""
        self.__ensure_document_database_exists()
        document = self.document_database.update_status(document_id, status)
        if file_path:
            document.file_path = str(file_path)
            document.save(update_fields=["file_path"])
        return document

    def __get_valid_file_path(self, document: DocumentModel) -> List[Path]:
        """Validate and get paths of a document. Supports multiple files."""
        if not document.file_path:
            self.logger.error(
                f"Document {document.pk} has no stored file path",
                source=Path(__file__).name,
                call_by=Path(__file__).name,
                method_call=self.__get_valid_file_path.__name__,
            )
            raise ValueError(f"Document {document.pk} has no stored file path")
        paths = []

        if isinstance(document.file_path, list):
            paths = [Path(p) for p in document.file_path]
        elif isinstance(document.file_path, str):
            paths = [Path(p.strip()) for p in document.file_path.split(",")]

        if not paths:
            raise ValueError(f"Document {document.pk} has invalid file paths")
        return paths

    # * New method to handle for new interface with file paths, this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
    def __execute_pipeline_create_retriever_with_paths(self, file_paths: list[Path], provider: EProviderName, model_name: str, embed_model_name: str) -> IGraphRagUploadResponse:
        # * Step 1: Extract text from files and normalize it, then store the extracted text in dict_contents
        contents, document_ids = self.__extract_contents_and_get_document_ids(file_paths, provider, file_caller=self.__execute_pipeline_create_retriever_with_paths.__name__)

        # * Step 2: Chunk and cache the normalized text
        chunk_responses, chunk_texts = self.__chunk(contents)
        chunk_batches = [chunk_response.chunk_texts for chunk_response in chunk_responses]

        # * Step 3: Create graph retriever
        responses = self.__create_graph_retriever(provider, document_ids, chunk_batches, model_name, embed_model_name)
        return responses

    def __create_graph_retriever(self, provider: EProviderName, document_ids: List[str], chunks_batches: List[List[str]], model_name: str, embed_model_name: str) -> IGraphRagUploadResponse:
        responses = []
        for document_id, chunk_texts in zip(document_ids, chunks_batches):
            graph_retriever = self.upload_job.step_build_knowledge_graph(
                document_id,
                chunk_texts,
                model_name,
                embed_model_name,
                provider,
                file_caller=self.__create_graph_retriever.__name__,
            )
            responses.append(graph_retriever)
        return IGraphRagUploadResponse(
            conversation_name=self.upload_job.build_name(document_ids, file_caller=self.__create_graph_retriever.__name__),
            responses=responses,
            created_at=np.datetime64("now"),
        )

    # * New method to handle for new interface with file paths, this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
    def __execute_base_pipeline_with_paths(
        self, file_paths: list[Path], provider: EProviderName, model_name: str
    ) -> IUploadResponse:

        # * Step 0: Create base model and get index on db for using like file name
        faiss_document = self.__create_document_model()

        # * Step 1: Extract text from files and normalize it, then store the extracted text in dict_contents and get document ids
        contents, document_ids = self.__extract_contents_and_get_document_ids(file_paths, provider, file_caller=self.__execute_base_pipeline_with_paths.__name__)

        # * Step 2: Chunk the normalized text
        chunk_responses, chunk_texts = self.__chunk(contents)

        # * Step 3: Embed the chunks
        embed_responses, embeddings = self.__embed_chunks(chunk_responses, provider)
        ids = np.concatenate([chunk_response.chunk_keys for chunk_response in chunk_responses]) if chunk_responses else np.array([], dtype=np.int64)

        # * Step 4: Cache the chunks and embeddings, and get the cache paths
        cache_responses = self.__cache(chunk_responses, embed_responses)
        chunk_paths = [cache_response.path for cache_response in cache_responses]
        cache_params = [cache_response.cache_param for cache_response in cache_responses]

        # * Step 5: Save the embeddings to vector store
        upload_response = self.upload_job.step_save(
            provider,
            faiss_document.faiss_index_id,
            document_ids,
            embeddings,
            chunk_texts,
            chunk_paths,
            ids,
            file_caller=self.__execute_base_pipeline_with_paths.__name__,
        )
        if upload_response is None:
            raise ValueError(f"Failed to save embeddings for provider {provider} and document ids: {document_ids}")

        # * Step 6: Sumarize the document and get the summary text
        summarize = self.upload_job.summarize_document(upload_response.faiss_index, upload_response.faiss_file_id, 
                                                       upload_response.embeddings_stack, cache_params, provider, model_name, file_caller=self.__execute_base_pipeline_with_paths.__name__)
        upload_response.summarize = summarize
        return upload_response

    # * Mini step on pipeline

    def __upload_to_vector_store(self, provider: EProviderName, document_ids: List[str], faiss_file_id: uuid.UUID,
                                 embedding_batches: List[np.ndarray], chunk_texts: List[str] = [], ids: np.ndarray = np.ndarray([], dtype=np.int64), chunk_paths: List[Path] = [], file_caller: str = "") -> IUploadResponse:
        try:            
            upload_response = self.upload_job.step_save(provider, faiss_file_id, document_ids, embedding_batches, chunk_texts, chunk_paths, ids, file_caller=self.__upload_to_vector_store.__name__)
            if upload_response is None:
                self.__update_document_status_and_path(faiss_file_id, EDocumentStatus.FAILED)
                raise ValueError(f"Failed to save embeddings for provider {provider} and document ids: {document_ids}")
        except Exception as exc:
            self.__update_document_status_and_path(faiss_file_id, EDocumentStatus.FAILED)
            self.logger.error(f"Error saving embeddings to vector store for document ids {document_ids} and provider {provider}: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.__upload_to_vector_store.__name__)
            raise exc
        self.__update_document_status_and_path(faiss_file_id, EDocumentStatus.INDEXED)
        return upload_response

    def __embed_chunks(self, chunk_responses: List[IChunkResponse], provider: EProviderName) -> Tuple[List[IEmbedResponse], List[np.ndarray]]:
        embed_responses = list[IEmbedResponse]()
        for chunk_response in chunk_responses:
            embed_response = self.upload_job.step_embed(chunk_response, provider, file_caller=self.__embed_chunks.__name__)
            embed_responses.append(embed_response)
        return embed_responses, [embed.embeddings for embed in embed_responses]

    def __chunk(self, contents: List[IExtractMapping]) -> Tuple[List[IChunkResponse], List[str]]:
        chunk_responses = list[IChunkResponse]()
        texts = []
        for content in contents:
            id = content.extract_content.document_id
            texts.append(content.extract_content.extracted_text)
            chunk_response = self.upload_job.step_chunk(id, texts[-1], file_caller=self.__chunk.__name__)
            chunk_responses.append(chunk_response)
        return chunk_responses, texts

    def __cache(self, chunk_responses: List[IChunkResponse], embedding_responses: List[IEmbedResponse]) -> List[IChunkAndCacheResponse]:
        cache_responses = []
        for chunk_response, embedding_response in zip(chunk_responses, embedding_responses):
            cache_response = self.upload_job.step_cache(chunk_response, embedding_response, file_caller=self.__cache.__name__)
            cache_responses.append(cache_response)
        return cache_responses

    def __extract_contents_and_get_document_ids(self, file_paths: list[Path], provider: EProviderName, file_caller: str = "") -> Tuple[List[IExtractMapping], List[str]]:
        contents = list[IExtractMapping]()
        for file_path in file_paths:
            self.logger.info(
                f"Extracting text from file {file_path}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.__extract_contents_and_get_document_ids.__name__,
            )
            extracted_text = self.upload_job.step_extract_and_normalize(file_path, provider, file_caller=self.__extract_contents_and_get_document_ids.__name__)
            contents.append(IExtractMapping(file_path, extracted_text))
        return contents, [content.extract_content.document_id for content in contents]
