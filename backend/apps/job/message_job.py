import hashlib
import time
from pathlib import Path
from typing import cast
import uuid
import numpy as np
import concurrent.futures

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.interfaces.dataclass.application.i_message_response import IMessageDTO
from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam, ICacheParamValue
from backend.apps.core.interfaces.dataclass.locate.i_neo4j_search_request import INeo4jSearchRequest
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.core.interfaces.services.cache.i_memory_pool import IMemoryPool
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import IConversationDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_file_database import IConversationFileDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_message_database import IMessageDatabase
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import IExtractContent
from backend.apps.core.interfaces.services.rag_base.locate.i_spare_vector_store_service import ISpareVectorStoreService
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_db_service import IVectorDBService
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import INeo4jService
from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService
from backend.apps.interfaces.job.i_message_job import IMessageJob
from backend.apps.core.interfaces.dataclass.job.i_message_job import IMessageJobResponse, IMessageJobContextHit
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, DocumentModel, MessageModel
from neo4j_graphrag.generation.prompts import RagTemplate

from sys_services.time_counter import TimeCounter
from tests import chunking_test

class MessageJob(IMessageJob):
    def __init__(self, llm_provider_factory: ILLMProviderFactory, config_provider: IConfigProvider, 
                 database_provider: IDatabaseProvider, prompt_structure: ILLMPromptStructure,
                 locate_service: ILocateService, cache_session: IConnectCacheSession, 
                 memory_pool: IMemoryPool,
                 logger: ILogger, hybrid_search_service: IHybridSearchService, extract_service: IExtractContent, neo4j_service: INeo4jService):
        self.llm_provider_factory = llm_provider_factory
        self.config_provider = config_provider
        self.database_provider = database_provider
        self.prompt_structure = prompt_structure
        self.locate_service = locate_service
        self.cache_session = cache_session
        self.logger = logger
        self.hybrid_search_service = hybrid_search_service
        self.memory_pool = memory_pool
        self.extract_service = extract_service
        self.neo4j_service = neo4j_service
        self.conversation_database = cast(IConversationDatabase, self.database_provider.get_model_service(ConversationModel))
        self.message_database = cast(IMessageDatabase, self.database_provider.get_model_service(MessageModel))
        self.conversation_files_database = cast(IConversationFileDatabase, self.database_provider.get_model_service(ConversationFilesModel))
        self.document_database = cast(IDocumentDatabase, self.database_provider.get_model_service(DocumentModel))

    def get_conversation(self, conversation_id: str) -> ConversationModel:
        return self.conversation_database.get_by_id(conversation_id)

    def save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        return self.message_database.create_message(conversation, is_user_send=is_user_send, content=content)

    def build_prompt_and_retrieve(self, content: str, conversation: ConversationModel, provider: EProviderName, pipeline_type: EPipelineType, model_name: str, embedding_model_name: str = "gemini-embedding-2") -> tuple[str, list[IMessageJobContextHit]]:
        context_hits: list[IMessageJobContextHit] = []
        context_hits_dicts: list[dict] = []

        if pipeline_type == EPipelineType.HYBRID:
            graph_context, context_hits = self.__thread_pool_executor_hybrid_search(content, conversation, provider, model_name, embedding_model_name)
            context_hits_dicts = [{"text": hit.text, "score": hit.score} for hit in context_hits]
            prompt = self.prompt_structure.build_prompt_for_graph_context(content, context_hits_dicts, graph_context)

        elif pipeline_type == EPipelineType.GRAPH:
            graph_context = self.__thread_pool_executor_graph_search(content, conversation, provider, embedding_model_name)
            prompt = self.prompt_structure.build_prompt_for_graph_context(content, context_hits_dicts, graph_context)

        else:
            context_hits = self.__retrieve_context_hits(content, conversation, provider, model_name, embedding_model_name)
            retrieval = [hit.text for hit in context_hits]
            prompt = self.prompt_structure.build_prompt(retrieval, content)

        return prompt, context_hits

    def generate_answer(self, provider: EProviderName, model_name: str, prompt: str) -> str:
        llm_client = self.llm_provider_factory.get_provider(provider)

        self.logger.info(
            f"Generating assistant response for provider={provider.value}",
            source=str(self.__class__),
            method_call=self.generate_answer.__name__,
        )

        response = llm_client.generate(ICompletionRequest(provider, model_name, prompt))
        return getattr(response, 'content', getattr(response, 'message_content', str(response)))

    def __thread_pool_executor_hybrid_search(self, content: str, conversation: ConversationModel, provider: EProviderName, model_name: str, embedding_model_name: str = "gemini-embedding-2") -> tuple[str, list[IMessageJobContextHit]]:
        # Khởi tạo 2 luồng công nhân (worker) chạy song song
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Giao việc cho công nhân 1 (Tìm Hybrid)
            future_hybrid = executor.submit(self.__retrieve_context_hits, content, conversation, provider, model_name, embedding_model_name)
            # Giao việc cho công nhân 2 (Tìm Graph)
            future_graph = executor.submit(self.__retrieve_graph_context, content, conversation, provider, embedding_model_name)

            # Thu thập kết quả (Hệ thống sẽ chờ đến khi cả 2 công nhân đều làm xong)
            context_hits = future_hybrid.result()
            graph_context = future_graph.result()

        self.logger.info(f"Parallel Retrieval completed", source=str(self.__class__))
        return (graph_context, context_hits)

    def __thread_pool_executor_vector_search(
        self, 
        conversation: ConversationModel, 
        content: str, 
        query_embedding: np.ndarray, 
        faiss_store: IVectorStoreService, 
        documents: list[ConversationFilesModel],
        bm25_store: ISpareVectorStoreService = None, #type: ignore
    ) -> tuple[list[IMessageJobContextHit], list[IMessageJobContextHit]]:

        all_dense_hits: list[IMessageJobContextHit] = []
        all_sparse_hits: list[IMessageJobContextHit] = []
        document = self.document_database.get_by_conversation(conversation)

        # ID dùng để search index (thường là ID của conversation hoặc document)        
        try:
            faiss_search = self.__faiss_search(conversation.conversations_id, query_embedding, faiss_store)
            all_dense_hits.extend(faiss_search)
        except Exception as exc:
            self.logger.error(f"FAISS search failed for conversation {conversation.conversations_id}: {exc}", Path(__file__).name, self.__thread_pool_executor_vector_search.__name__)

        # Sắp xếp lại danh sách kết quả theo điểm số giảm dần
        all_dense_hits.sort(key=lambda item: item.score, reverse=True)
        all_sparse_hits.sort(key=lambda item: item.score, reverse=True)

        return all_dense_hits, all_sparse_hits

    def __thread_pool_executor_graph_search(self, content: str, conversation: ConversationModel, provider: EProviderName, embedding_model_name: str) -> str:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_graph = executor.submit(self.__retrieve_graph_context, content, conversation, provider, embedding_model_name)
            graph_context = future_graph.result()
        return graph_context

    def __retrieve_context_hits(self, content: str, conversation: ConversationModel, provider: EProviderName, model_name: str, embedding_model_name: str) -> list[IMessageJobContextHit]:
        """Đã Tuning: Gọi song song (Concurrency) hàng loạt file để tránh nghẽn I/O"""
        files = self.conversation_files_database.get_by_conversation(conversation)
        self.logger.info(f"Retrieved {len(files)} files for conversation {conversation.conversations_id}", source=str(self.__class__), method_call=self.__retrieve_context_hits.__name__)
        documents = [f for f in files if f.conversation_files_id and f.conversation_files_document.documents_status == "indexed"]
        if not documents:
            return []
        self.logger.info(f"Filtered {len(documents)} indexed documents for conversation {conversation.conversations_id}", source=str(self.__class__), method_call=self.__retrieve_context_hits.__name__)
        query_embedding = self.__embed_text(content, provider, embedding_model_name)
        faiss_store = cast(IVectorStoreService, self.locate_service.get_vector_store(EBackendStorageName.FAISS))
        # bm25_store = cast(ISpareVectorStoreService, self.locate_service.get_vector_store(EBackendStorageName.BM25))
        all_dense_hits, all_sparse_hits = self.__thread_pool_executor_vector_search(conversation, content, query_embedding, faiss_store, documents)

        self.logger.info(f"Fusing {len(all_dense_hits)} Dense and {len(all_sparse_hits)} Sparse hits", Path(__file__).name, Path(__file__).name, self.__retrieve_context_hits.__name__)
        return all_dense_hits
        # return self.hybrid_search_service.fuse_results(all_dense_hits, all_sparse_hits, top_k=5)

    def __retrieve_graph_context(
        self,
        content: str,
        conversation: ConversationModel,
        provider: EProviderName,
        embedding_model_name: str,
    ) -> str:
        try:
            files = self.conversation_files_database.get_by_conversation(conversation)
            embedder = self.llm_provider_factory.get_provider(
                EProviderName.GEMINI
            ).get_embedder_model("gemini-embedding-2")
            if not files.exists():
                return ""
            llm_client = self.llm_provider_factory.get_provider(EProviderName.GEMINI).get_llm_model(
                "gemini-3.1-flash-lite"
            )
            graph_retriever = self.neo4j_service.create_graph_retriever(
                template=self.prompt_structure.build_prompt_for_retrieval_query(),
                embedder=embedder,
                index_name=conversation.conversations_id,
            )
            request = INeo4jSearchRequest(content, top_k=5)
            search_results = self.neo4j_service.search(
                request,
                llm_client,
                graph_retriever,
                self.prompt_structure.create_rag_template(),
                file_caller=self.__retrieve_graph_context.__name__,
            )
            return search_results
        except Exception as exc:
            self.logger.error(
                f"Error retrieving conversation files for graph context: {exc}",
                source=str(self.__class__),
                method_call=self.__retrieve_graph_context.__name__,
            )
            return ""

    def __embed_text(self, text: str, provider: EProviderName, embedding_model_name: str) -> np.ndarray:
        llm_client = self.llm_provider_factory.get_provider(provider)
        response = llm_client.embedding(ICompletionRequest(provider=provider, model=embedding_model_name, prompt=text))
        return response.embedding.astype(np.float32)

    def __load_document_chunk_metadata(self, conversation_id: uuid.UUID) -> list[ICacheParamValue]:
        # Ghi log file_caller cho Cache Service
        try:
            cache_service = self.cache_session.connect(file_caller=self.__load_document_chunk_metadata.__name__)
            self.logger.info(f"Connected to cache service for conversation_id {conversation_id}", Path(__file__).name, self.__load_document_chunk_metadata.__name__)
            if not isinstance(cache_service, ICacheService):
                raise ValueError("Cache service connection failed or returned invalid type")
            response = cache_service.get(str(conversation_id), file_caller=self.__load_document_chunk_metadata.__name__)
            if response and response.values:
                return response.values
            else:
                response = cache_service.load_from_file(str(conversation_id), file_caller=self.__load_document_chunk_metadata.__name__)
                if response and response.values:
                    return response.values
            raise ValueError(f"No cache data found for conversation_id {conversation_id}")
        finally:
            self.cache_session.disconnect(file_caller=self.__load_document_chunk_metadata.__name__)

    def __get_attached_document_texts(self, conversation: ConversationModel) -> list[str]:
        """
        Thu thập toàn bộ nội dung văn bản thô của các tài liệu đính kèm phục vụ luồng fallback keyword match.
        Sử dụng extract_service chuẩn IoC khi Redis cache bị mất hoặc hết hạn dữ liệu (Eviction).
        """
        document_texts: list[str] = []

        # Tìm tất cả các liên kết file với Conversation hiện tại
        mappings = self.conversation_files_database.get_by_conversation(conversation)

        for mapping in mappings:
            file_id = mapping.conversation_files_id
            document = mapping.conversation_files_document
            if file_id is None or document.documents_status != "indexed":
                continue
            id = conversation.conversations_id
            # Thử tải dữ liệu chunks từ Redis cache trước để tối ưu tốc độ RAM
            meta = self.__load_document_chunk_metadata(id)
            if meta is not None:
                chunks_dict = {text.index: text.text_value for text in meta}
                # Sắp xếp các phân đoạn theo thứ tự index tăng dần (doc_id:1, doc_id:2...) để văn bản liền mạch
                full_text = "\n".join(chunks_dict[k] for k in sorted(chunks_dict.keys()))
                document_texts.append(full_text)
                continue

            # FALLBACK: Nếu Redis trống, sử dụng đúng self.extract_service để bóc tách lại file vật lý từ ổ cứng
            if document.documents_file_path:
                file_path = Path(document.documents_file_path)
                if file_path.exists():
                    try:
                        # Tiến hành trích xuất sử dụng đúng service đã được inject qua Container
                        raw_texts = self.extract_service.extract(file_path, EProviderName.MISTRAL)
                        if raw_texts and raw_texts.extracted_text:
                            document_texts.append(raw_texts.extracted_text)
                            self.logger.info(f"Fallback text extraction successful for conversation {id}", source=str(self.__class__))
                    except Exception as exc:
                        self.logger.error(
                            f"Fallback text extraction failed for conversation {id}: {exc}",
                            source=str(self.__class__),
                            method_call=self.__get_attached_document_texts.__name__
                        )
        return document_texts

    def __resolve_chunk_texts(self, indices: list[np.int64], metadata: list[ICacheParamValue]) -> list[str]:
        chunk_texts: list[str] = []
        index_per_rows = {meta.index: meta.text_value for meta in metadata}
        for idx in indices:
            if idx in index_per_rows:
                chunk_texts.append(index_per_rows[idx])
        return chunk_texts

    def __faiss_search(self, conversation_id: uuid.UUID, query_embedding: np.ndarray, faiss_store: IVectorStoreService) -> list[IMessageJobContextHit]:
        dense_hits: list[IMessageJobContextHit] = []
        meta = self.__load_document_chunk_metadata(conversation_id)
        load_faiss = None
        try:
            load_faiss = self.memory_pool.get_from_pool(conversation_id)
        except Exception as exc:
            self.logger.error(f"Error occurred while fetching FAISS index for conversation {conversation_id}: {exc}", source=str(self.__class__), method_call=self.__faiss_search.__name__)
            load_faiss = faiss_store.load(conversation_id, file_caller=self.__faiss_search.__name__)
            if load_faiss.is_success and load_faiss.index is not None:
                self.memory_pool.add_to_pool(conversation_id, load_faiss.index)
                self.logger.info(f"FAISS index for conversation {conversation_id} added to memory pool", source=str(self.__class__), method_call=self.__faiss_search.__name__)
        
        if load_faiss:
            query_res = faiss_store.search(load_faiss, conversation_id, query_embedding, limit=5, file_caller=self.__faiss_search.__name__)
            self.logger.info(f"FAISS search returned {len(query_res.indices)} hits for conversation {conversation_id}", source=str(self.__class__), method_call=self.__faiss_search.__name__)
            chunk_texts = self.__resolve_chunk_texts(query_res.indices, meta)
            self.logger.info(f"Resolved {len(chunk_texts)} chunk texts for conversation {conversation_id}", source=str(self.__class__), method_call=self.__faiss_search.__name__)
            for distance in query_res.distances:
                # Truyền base_id đã tính ở trên xuống
                similarity = 1.0 / (1.0 + float(distance))
                dense_hits.append(IMessageJobContextHit(text="", score=similarity, source_document_id=str(conversation_id)))
            for text, dense_hit in zip(chunk_texts, dense_hits):
                dense_hit.text = text
        return dense_hits

    def __bm25_search(self, conversation_id: uuid.UUID, content: str, bm25_store: ISpareVectorStoreService) -> list[IMessageJobContextHit]:
        sparse_hits: list[IMessageJobContextHit] = []
        meta = self.__load_document_chunk_metadata(conversation_id)
        load_bm25 = bm25_store.load(conversation_id, file_caller=self.__bm25_search.__name__)
        if load_bm25.is_success and load_bm25.index is not None:
            bm25_res = bm25_store.search(load_bm25.index, conversation_id, query_text=content, limit=5, file_caller=self.__bm25_search.__name__)
            self.logger.info(f"BM25 search returned {len(bm25_res.indices)} hits for conversation {conversation_id}", source=str(self.__class__), method_call=self.__bm25_search.__name__)
            chunk_texts = self.__resolve_chunk_texts(bm25_res.indices, meta)
            self.logger.info(f"Resolved {len(chunk_texts)} chunk texts for conversation {conversation_id}", source=str(self.__class__), method_call=self.__bm25_search.__name__)
            for distance in bm25_res.distances:
                # Truyền base_id đã tính ở trên xuống
                similarity = 1.0 / (1.0 + float(distance))
                sparse_hits.append(IMessageJobContextHit(text="", score=similarity, source_document_id=str(conversation_id)))
            for text, spare_hit in zip(chunk_texts, sparse_hits):
                spare_hit.text = text
        return sparse_hits

    def get_conversation_title(self, conversation_id: str) -> str:
        conversation = self.conversation_database.get_by_id(conversation_id)
        self.logger.info(f"Retrieved conversation title for {conversation_id}: {conversation.conversations_title}", Path(__file__).name, self.get_conversation_title.__name__)
        return conversation.conversations_title

    def get_messages(self, conversation_id: str, limit: int, offset: int) -> list[IMessageDTO]:
        self.logger.info(f"Fetching messages for conversation {conversation_id} with limit={limit} and offset={offset}", Path(__file__).name, self.get_messages.__name__)
        conversation = self.conversation_database.get_by_id(conversation_id)
        self.logger.info(f"Retrieved conversation for {conversation_id}: {conversation.conversations_title}", Path(__file__).name, self.get_messages.__name__)

        # Lấy dữ liệu từ DB Service
        messages_qs = self.message_database.get_by_conversation(conversation)
        self.logger.info(f"Retrieved {messages_qs.count()} messages for conversation {conversation_id}", Path(__file__).name, self.get_messages.__name__)
        paginated_qs = messages_qs.order_by("-messages_created_at")[offset : offset + limit]
        self.logger.info(f"Paginated messages: {len(paginated_qs)} messages returned for conversation {conversation_id}", Path(__file__).name, self.get_messages.__name__)
        # MAP ORM MODEL SANG DTO
        dtos = []
        for m in reversed(paginated_qs):
            dto = IMessageDTO(
                id=str(
                    m.messages_id
                ),  # Thay bằng tên trường id thực tế trong Model của bạn
                conversation_id=str(conversation_id),
                role="user" if m.messages_is_user_send else "assistant",
                content=m.messages_content,
                created_at=m.messages_created_at.isoformat(),
            )
            dtos.append(dto)
            self.logger.info(f"dto created for message {m.messages_id} in conversation {conversation_id}: {dto}", Path(__file__).name, self.get_messages.__name__)
            self.logger.info(f"Mapped message {m.messages_id} to DTO for conversation {conversation_id}", Path(__file__).name, self.get_messages.__name__)
        self.logger.info(f"Total DTOs created: {len(dtos)} for conversation {conversation_id}", Path(__file__).name, self.get_messages.__name__)
        return dtos

    def count_messages(self, conversation_id: str) -> int:
        conversation = self.conversation_database.get_by_id(conversation_id)
        self.logger.info(f"Counting messages for conversation {conversation_id}", Path(__file__).name, self.count_messages.__name__)
        self.logger.info(f"Retrieved message count for conversation {conversation_id}: {self.message_database.get_by_conversation(conversation).count()}", Path(__file__).name, self.count_messages.__name__)
        count = self.message_database.get_by_conversation(conversation).count()
        self.logger.info(f"Final message count for conversation {conversation_id}: {count}", Path(__file__).name, self.count_messages.__name__)
        return count
    