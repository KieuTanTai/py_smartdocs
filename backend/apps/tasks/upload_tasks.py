"""
Upload tasks module.
Handles the execution flow for uploaded files via background workers.
"""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Any, cast
from pathlib import Path
import uuid
from celery import Task
import numpy as np

from backend.apps.core.enums.e_document_status import EDocumentStatus
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import ICacheResponse, IChunkResponse
from backend.apps.core.interfaces.services.cache.i_memory_pool import IMemoryPool
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import IConversationDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_file_database import IConversationFileDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.dataclass.tasks.i_upload_response import IEmbedResponse, IExtractMapping, IGraphRagParam, IGraphRagUploadResponse, IUploadResponse
from backend.apps.core.interfaces.system.i_time_counter import ITimeCounter
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, DocumentModel
from backend.apps.interfaces.tasks.i_upload_task import IUploadTask
from backend.apps.interfaces.job.i_upload_job import IUploadJob

class UploadTask(IUploadTask):

    def __init__(
        self,
        upload_job: IUploadJob,
        memory_pool: IMemoryPool,
        database_provider: IDatabaseProvider,
        logger: ILogger,
        time_counter: ITimeCounter,
    ):
        self.upload_job = upload_job
        self.logger = logger
        self.memory_pool = memory_pool
        self.database_provider = database_provider
        self.time_counter = time_counter
        self.document_database: IDocumentDatabase = cast(IDocumentDatabase, self.database_provider.get_model_service(DocumentModel))
        self.conversation_files_database = cast(IConversationFileDatabase, self.database_provider.get_model_service(ConversationFilesModel))
        self.conversation_database = cast(IConversationDatabase, self.database_provider.get_model_service(ConversationModel))

    # --- MAIN ENTRY POINT ---
    @property
    def name(self) -> str:
        """Return the task name for routing."""
        self.logger.info(f"Retrieving task name for routing", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.name)
        return Path(__file__).stem  # Dynamic name based on filename

    # * New run method to handle for new interface with file paths,
    # * this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
    def run_with_paths(self, conversation_id: uuid.UUID, file_paths: list[Path], provider_name: EProviderName, model_name: str, file_name: str, file_caller: str = "") -> IUploadResponse:
        self.logger.info(f"Starting UploadTask with file paths {file_paths} and provider {provider_name} called by {file_caller}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
        try:
            # Chạy luồng lõi
            conversation_model = self.conversation_database.get_by_id(conversation_id)
            print("path: ", conversation_model.conversations_id)
            result_dataclass = self.__execute_base_pipeline_with_paths(conversation_model, file_paths, provider_name, model_name, file_name)
            # Lưu index vào memory pool
            self.logger.info(f"Adding FAISS index to memory pool with file ID {result_dataclass.conversation_id} for file paths {file_paths}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
            self.memory_pool.add_to_pool(result_dataclass.conversation_id, result_dataclass.faiss_index, file_caller)
            self.logger.info(f"Successfully completed UploadTask for file paths {file_paths} and provider {provider_name}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
            return result_dataclass
        except Exception as exc:
            self.logger.error(f"Error processing file paths {file_paths}: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_with_paths.__name__)
            raise exc

    async def run_graph_pipeline_with_paths(self, conversation_id: uuid.UUID, file_paths: list[Path], provider_name: EProviderName, embed_model_name: str, model_name: str, file_caller: str = "") -> IGraphRagUploadResponse:
        self.logger.info(f"Starting Graph RAG UploadTask with file paths {file_paths} and provider {provider_name} called by {file_caller}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_graph_pipeline_with_paths.__name__)
        try:
            conversation_model = self.conversation_database.get_by_id(conversation_id)
            responses = await self.__execute_pipeline_create_retriever_with_paths(conversation_model, file_paths, provider_name, model_name, embed_model_name)
            self.logger.info(f"Successfully completed Graph RAG UploadTask for file paths {file_paths} and provider {provider_name}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_graph_pipeline_with_paths.__name__)
            return responses
        except Exception as exc:
            self.logger.error(f"Error processing file paths {file_paths} for graph pipeline: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.run_graph_pipeline_with_paths.__name__)
            raise exc

    def list_files(self, conversation_id: str, file_caller: str = "") -> list[ConversationFilesModel]:
        self.logger.info(f"Listing files for conversation_id: {conversation_id}", source=Path(__file__).name, call_by=file_caller, method_call=self.list_files.__name__)
        try:
            conversation_model = self.conversation_database.get_by_id(conversation_id)
            response = self.upload_job.list_files(conversation_model, file_caller=self.list_files.__name__)
            self.logger.info(f"Successfully listed files for conversation_id: {conversation_id}", source=Path(__file__).name, call_by=file_caller, method_call=self.list_files.__name__)
            return response
        except Exception as e:
            self.logger.error(f"Error listing files for conversation_id: {conversation_id}, error: {str(e)}", source=Path(__file__).name, call_by=file_caller, method_call=self.list_files.__name__)
            raise e

    # --- SINGLE RESPONSIBILITY METHODS ---

    def __create_document_model(self, conversation_model: ConversationModel, file_path: Path | None = None, content: str | None = None) -> DocumentModel:
        """Create a new document model and set its status."""
        # self.__ensure_document_database_initialized()
        response = self.document_database.create_document(conversation_model, file_path, EDocumentStatus.PROCESSING, content)
        self.logger.info(f"Created document model with ID {response.pk} for conversation {conversation_model.pk} and file path {file_path}", source=Path(__file__).name, call_by=self.__create_document_model.__name__, method_call=self.__create_document_model.__name__)
        return response

    def __update_document_status_and_path(self, document_id: Any, status: EDocumentStatus, file_path: Path | None = None) -> DocumentModel:
        """Update the document status and optionally its file path."""
        # if (self.document_database is None):
        #     self.__ensure_document_database_initialized()
        self.logger.info(f"Updating document model with ID {document_id} to status {status} and file path {file_path}", source=Path(__file__).name, call_by=self.__update_document_status_and_path.__name__, method_call=self.__update_document_status_and_path.__name__)
        document = self.document_database.update_status(document_id, status) 
        if file_path:
            document.documents_file_path = str(file_path)
            document.save(update_fields=["file_path"])
        self.logger.info(f"Updated document model with ID {document.pk} and file path {file_path}", source=Path(__file__).name, call_by=self.__update_document_status_and_path.__name__, method_call=self.__update_document_status_and_path.__name__)
        return document

    def __create_conversation_file_model(self, documents: list[tuple[DocumentModel, str]]) -> list[ConversationFilesModel]:
        self.logger.info(f"Creating conversation file models for documents: {[doc.pk for doc, _ in documents]}", source=Path(__file__).name, call_by=self.__create_conversation_file_model.__name__, method_call=self.__create_conversation_file_model.__name__)
        response = self.conversation_files_database.create_conversation_files_bulk(documents)
        self.logger.info(f"Created conversation file models with IDs: {[cfm.pk for cfm in response]}", source=Path(__file__).name, call_by=self.__create_conversation_file_model.__name__, method_call=self.__create_conversation_file_model.__name__)
        return response

    # * New method to handle for new interface with file paths, this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
    async def __execute_pipeline_create_retriever_with_paths(self, conversation_model: ConversationModel, file_paths: list[Path], provider: EProviderName, model_name: str, embed_model_name: str) -> IGraphRagUploadResponse:

        # start extract time counter
        self.time_counter.reset()
        self.time_counter.start()
        # * Step 1: Extract text from files and normalize it, then store the extracted text in dict_contents and get document ids
        document = self.__create_document_model(conversation_model)
        contents, document_ids = self.__extract_contents_and_get_document_ids(file_paths, provider, "", file_caller=self.__execute_pipeline_create_retriever_with_paths.__name__)
        extract_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed text extraction and normalization for file paths {file_paths} in {extract_time:.2f} seconds", source=Path(__file__).name, 
                         call_by=self.__execute_pipeline_create_retriever_with_paths.__name__, method_call=self.__execute_pipeline_create_retriever_with_paths.__name__)
        # start chunk time counter
        # * Step 2: Chunk the normalized text
        chunk_responses, chunk_texts = self.__chunk(contents)
        chunk_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed text chunking for file paths {file_paths} in {chunk_time:.2f} seconds", source=Path(__file__).name, 
                         call_by=self.__execute_pipeline_create_retriever_with_paths.__name__, method_call=self.__execute_pipeline_create_retriever_with_paths.__name__)

        # * Step 3: Cache the chunks
        cache_response = self.__cache(conversation_model.conversations_id, chunk_responses)

        # start graph retriever time counter
        # * Step 3: Create graph retriever
        graph_params = self.__build_list_graph_params(conversation_model, chunk_responses)
        graph_retriever_response = await self.__create_graph_retriever(conversation_model, provider, graph_params, model_name, embed_model_name)
        graph_retriever_response.conversation_files = self.__create_conversation_file_model(self.__build_documents(document_ids, document))
        graph_retriever_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed graph retriever creation for file paths {file_paths} in {graph_retriever_time:.2f} seconds", source=Path(__file__).name,   
                        call_by=self.__execute_pipeline_create_retriever_with_paths.__name__, method_call=self.__execute_pipeline_create_retriever_with_paths.__name__)
        graph_retriever_response.time_counter = self.time_counter.mapping_to_graph_time_counter_response(extract_time, chunk_time, graph_retriever_time)
        graph_retriever_response.conversation_cache_path = cache_response.path
        return graph_retriever_response

    def __build_list_graph_params(self, conversation_model: ConversationModel, chunk_responses: list[IChunkResponse]) -> list[IGraphRagParam]:
        graph_params = []
        for chunk_response in chunk_responses:
            for chunk_content, chunk_key in zip(chunk_response.chunk_texts, chunk_response.chunk_keys):
                graph_param = IGraphRagParam(
                    conversation_id=conversation_model.pk,
                    document_id=chunk_response.document_id,
                    chunk_content=chunk_content,
                    chunk_id=chunk_key
                )
                graph_params.append(graph_param)
        return graph_params

    async def __create_graph_retriever(self, conversation: ConversationModel, provider: EProviderName, list_params: list[IGraphRagParam], model_name: str, embed_model_name: str) -> IGraphRagUploadResponse:
        graph_retriever_response = await self.upload_job.step_build_knowledge_graph(
            conversation_id=conversation.pk,
            graph_params=list_params,
            model_name=model_name,
            embedding_model_name=embed_model_name,
            provider=provider,
            file_caller=self.__create_graph_retriever.__name__
        )
        if graph_retriever_response is None or isinstance(graph_retriever_response, IGraphRagUploadResponse) is False:
            self.logger.error(f"Failed to create graph retriever for conversation {conversation.pk} and provider {provider}", source=Path(__file__).name, call_by=self.__create_graph_retriever.__name__, method_call=self.__create_graph_retriever.__name__)
            raise ValueError(f"Failed to create graph retriever for conversation {conversation.pk} and provider {provider}")
        graph_retriever_response.conversation_name = conversation.conversations_name
        return graph_retriever_response

    # * New method to handle for new interface with file paths, this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
    def __execute_base_pipeline_with_paths(
        self, conversation_model: ConversationModel, file_paths: list[Path], provider: EProviderName, model_name: str, file_name: str
    ) -> IUploadResponse:
        print(f"Provider name: {provider.value} : {provider}")
        # start extract time counter
        self.time_counter.reset()
        self.time_counter.start()
        # * Step 0: Create base model and get index on db for using like file name
        document = self.__create_document_model(conversation_model)

        # * Step 1: Extract text from files and normalize it, then store the extracted text in dict_contents and get document ids
        contents, document_ids = self.__extract_contents_and_get_document_ids(file_paths, provider, file_name, file_caller=self.__execute_base_pipeline_with_paths.__name__)
        extract_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed text extraction and normalization for file paths {file_paths} in {extract_time:.2f} seconds", source=Path(__file__).name, 
                         call_by=self.__execute_base_pipeline_with_paths.__name__, method_call=self.__execute_base_pipeline_with_paths.__name__)

        # start chunk time counter
        # * Step 2: Chunk the normalized text
        chunk_responses, chunk_texts = self.__chunk(contents)
        chunk_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed text chunking for file paths {file_paths} in {chunk_time:.2f} seconds", source=Path(__file__).name, 
                         call_by=self.__execute_base_pipeline_with_paths.__name__, method_call=self.__execute_base_pipeline_with_paths.__name__)

        # start embedding time counter
        # * Step 3: Embed the chunks
        embed_responses, embeddings = self.__embed_chunks(chunk_responses, provider)
        ids = np.concatenate([chunk_response.chunk_keys for chunk_response in chunk_responses]) if chunk_responses else np.array([], dtype=np.int64)
        embedding_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed text embedding for file paths {file_paths} in {embedding_time:.2f} seconds", source=Path(__file__).name, 
                         call_by=self.__execute_base_pipeline_with_paths.__name__, method_call=self.__execute_base_pipeline_with_paths.__name__)

        # start save time counter
        # * Step 4: Cache the chunks and embeddings, and get the cache paths
        print("cache step", conversation_model.conversations_id)
        cache_response = self.__cache(conversation_model.conversations_id, chunk_responses)
        cache_param_values  = cache_response.cache_param.values

        # * Step 5: Save the embeddings to vector store and update document model with file path and status
        try:
            upload_response = self.__upload_to_vector_store(provider, document_ids, conversation_model.conversations_id, document.document_id, embeddings, chunk_texts, ids, file_caller=self.__execute_base_pipeline_with_paths.__name__)
            upload_response.conversation_files = self.__create_conversation_file_model(self.__build_documents(document_ids, document))
            upload_response.conversation_cache_path = cache_response.path
        except Exception as exc:
            self.time_counter.stop()
            self.time_counter.reset()
            self.logger.error(f"Error during saving embeddings to vector store for file paths {file_paths}: {exc}", source=Path(__file__).name, call_by=self.__execute_base_pipeline_with_paths.__name__, method_call=self.__execute_base_pipeline_with_paths.__name__)
            raise exc

        save_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed saving embeddings to vector store for file paths {file_paths} in {save_time:.2f} seconds", source=Path(__file__).name, 
                         call_by=self.__execute_base_pipeline_with_paths.__name__, method_call=self.__execute_base_pipeline_with_paths.__name__)

        # start summarize time counter
        # * Step 6: Sumarize the document and get the summary text
        print("SI<<")
        # summarize = self.upload_job.summarize_document(upload_response.faiss_index, upload_response.conversation_id, cache_param_values, provider, model_name, file_caller=self.__execute_base_pipeline_with_paths.__name__)
        # upload_response.summarize = ""
        summarize_time = self.time_counter.get_elapsed_time()
        self.logger.info(f"Completed document summarization for file paths {file_paths} in {summarize_time:.2f} seconds", source=Path(__file__).name, 
                         call_by=self.__execute_base_pipeline_with_paths.__name__, method_call=self.__execute_base_pipeline_with_paths.__name__)

        # * Step 7: mapping time counter to response
        list_cloud_id_pairs: list[tuple[DocumentModel, str]] = []
        for id in document_ids:
            list_cloud_id_pairs.append((document, id))
        self.conversation_files_database.create_conversation_files_bulk(list_cloud_id_pairs)
        upload_response.time_counter = self.time_counter.mapping_to_time_counter_response(extract_time, chunk_time, embedding_time, save_time, summarize_time)
        upload_response.conversation_id = conversation_model.pk
        upload_response.conversation_name = conversation_model.conversations_name
        return upload_response


    # * Mini step on pipeline
    def __build_documents(self, document_ids: list[str], document: DocumentModel) -> list[tuple[DocumentModel, str]]:
        self.logger.info(f"Building document tuples for document IDs: {document_ids} and document model ID: {document.pk}", source=Path(__file__).name, call_by=self.__build_documents.__name__, method_call=self.__build_documents.__name__)
        result = [(document, doc_id) for doc_id in document_ids]
        self.logger.info(f"Built document tuples: {[(doc.pk, doc_id) for doc, doc_id in result]}", source=Path(__file__).name, call_by=self.__build_documents.__name__, method_call=self.__build_documents.__name__)
        return result

    def __upload_to_vector_store(self, provider: EProviderName, document_ids: list[str], conversation_id: uuid.UUID,
                                document_id: uuid.UUID,
                                 embedding_batches: list[np.ndarray], chunk_texts: list[str] = [], ids: np.ndarray = np.ndarray([], dtype=np.int64), file_caller: str = "") -> IUploadResponse:
        try:            
            upload_response = self.upload_job.step_save(provider, conversation_id, document_ids, embedding_batches, chunk_texts, ids, file_caller=self.__upload_to_vector_store.__name__)
            print(upload_response)
            if upload_response is None:
                self.__update_document_status_and_path(document_id, EDocumentStatus.FAILED)
                raise ValueError(f"Failed to save embeddings for provider {provider} and document ids: {document_ids}")
        except Exception as exc:
            self.__update_document_status_and_path(document_id, EDocumentStatus.FAILED)
            self.logger.error(f"Error saving embeddings to vector store for document ids {document_ids} and provider {provider}: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.__upload_to_vector_store.__name__)
            raise exc
        self.__update_document_status_and_path(document_id, EDocumentStatus.INDEXED)
        return upload_response

    def __embed_chunks(self, chunk_responses: list[IChunkResponse], provider: EProviderName) -> tuple[list[IEmbedResponse], list[np.ndarray]]:
        embed_responses = list[IEmbedResponse]()
        for chunk_response in chunk_responses:
            embed_response = self.upload_job.step_embed(chunk_response, provider, file_caller=self.__embed_chunks.__name__)
            embed_responses.append(embed_response)
        return embed_responses, [embed.embeddings for embed in embed_responses]

    def __chunk(self, contents: list[IExtractMapping]) -> tuple[list[IChunkResponse], list[str]]:
        chunk_responses = list[IChunkResponse]()
        texts = []
        for content in contents:
            id = content.extract_content.document_id
            texts.append(content.extract_content.extracted_text)
            chunk_response = self.upload_job.step_chunk(id, texts[-1], file_caller=self.__chunk.__name__)
            chunk_responses.append(chunk_response)
        return chunk_responses, texts

    def __cache(self, conversation_id: uuid.UUID, chunk_responses: list[IChunkResponse]) -> ICacheResponse:
        cache_response = self.upload_job.step_cache(conversation_id, chunk_responses, file_caller=self.__cache.__name__)
        return cache_response

    def __extract_contents_and_get_document_ids(self, file_paths: list[Path], provider: EProviderName, file_name: str, file_caller: str = "") -> tuple[list[IExtractMapping], list[str]]:
        contents = list[IExtractMapping]()
        lens = len(file_paths)
        with ThreadPoolExecutor(max_workers=lens) as executor:
            futures = {executor.submit(self.upload_job.step_extract, file_path, provider, file_name, file_caller): file_path for file_path in file_paths}
            for future in as_completed(futures):
                try:
                    content = IExtractMapping(futures[future], future.result())
                    contents.append(content)
                except Exception as exc:
                    self.logger.error(f"Error extracting content from {futures[future]}: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.__extract_contents_and_get_document_ids.__name__)
                    raise exc
        return contents, [content.extract_content.document_id for content in contents]
