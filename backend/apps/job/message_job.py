import hashlib
import time
from pathlib import Path
from typing import List
import numpy as np
import concurrent.futures

from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import IExtractContent
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
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, MessageModel
from neo4j_graphrag.generation.prompts import RagTemplate

from sys_services.time_counter import TimeCounter

class MessageJob(IMessageJob):
    def __init__(self, llm_provider_factory: ILLMProviderFactory, config_provider: IConfigProvider, locate_service: ILocateService, cache_session: IConnectCacheSession, logger: ILogger, hybrid_search_service: IHybridSearchService, extract_service: IExtractContent, neo4j_service: INeo4jService):
        self.llm_provider_factory = llm_provider_factory
        self.config_provider = config_provider
        self.locate_service = locate_service
        self.cache_session = cache_session
        self.logger = logger
        self.hybrid_search_service = hybrid_search_service
        self.extract_service = extract_service
        self.neo4j_service = neo4j_service

    def run(self, conversation_id: str, content: str, provider: EProviderName, model_name: str | None = None) -> IMessageJobResponse:
        total_timer = TimeCounter()
        total_timer.start()
        
        conversation = self._get_conversation(conversation_id)
        
        # Lưu tin nhắn của user
        self._save_message(conversation, is_user_send=True, content=content)
    
        # Khởi tạo 2 luồng công nhân (worker) chạy song song
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Giao việc cho công nhân 1 (Tìm Hybrid)
            future_hybrid = executor.submit(self._retrieve_context_hits, content, conversation, provider)
            # Giao việc cho công nhân 2 (Tìm Graph)
            future_graph = executor.submit(self._retrieve_graph_context, content, conversation, provider)

            # Thu thập kết quả (Hệ thống sẽ chờ đến khi cả 2 công nhân đều làm xong)
            context_hits = future_hybrid.result()
            graph_context = future_graph.result()
            
        self.logger.info(f"Parallel Retrieval completed", source=str(self.__class__))

        context_hits_dicts = [{"text": hit.text, "score": hit.score} for hit in context_hits]
        
        # Gộp cả 2 vào Prompt
        prompt = self._build_prompt(content, context_hits_dicts, graph_context)

        model = model_name or "qwen2.5:1.5b-instruct"
        llm_client = self.llm_provider_factory.get_provider(provider)

        self.logger.info(
            f"Generating assistant response for conversation={conversation_id} provider={provider.value}",
            source=str(self.__class__),
            method_call=self.run.__name__,
        )

        
        response = llm_client.generate(ICompletionRequest(provider=provider, model=model, prompt=prompt, context_hits=context_hits_dicts))

        # Lưu tin nhắn của Assistant
        self._save_message(conversation, is_user_send=False, content=response)

        return IMessageJobResponse(
            conversation_id=str(conversation.conversation_id),
            assistant=response,
            provider=provider.value,
            model=model,
            retrieval_hits=context_hits
        )
        
        # metrics = ITimeConversationCounter(
        #     conversation_id=conversation_id,
        #     llm_time_ms=llm_timer.get_elapsed_time_ms(),
        #     retrieval_time_ms=retrieval_timer.get_elapsed_time_ms(),
        #     other_time_ms=(total_timer.get_elapsed_time_ms() - llm_timer.get_elapsed_time_ms() - retrieval_timer.get_elapsed_time_ms()),
        #     total_time_ms=total_timer.get_elapsed_time_ms()
        # )

    def _get_conversation(self, conversation_id: str) -> ConversationModel:
        try:
            return ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist as exc:
            raise ValueError(f"Conversation not found: {conversation_id}") from exc

    def _save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        return MessageModel.objects.create(message_conversation=conversation, message_is_user_send=is_user_send, message_content=content)

    def _retrieve_context_hits(self, content: str, conversation: ConversationModel, provider: EProviderName) -> list[IMessageJobContextHit]:
        """Đã Tuning: Gọi song song (Concurrency) hàng loạt file để tránh nghẽn I/O"""
        mappings = ConversationFilesModel.objects.filter(conversation=conversation)
        valid_documents = [m.faiss_index for m in mappings if m.faiss_index and m.faiss_index.status == "indexed"]
        
        if not valid_documents:
            return []

        query_embedding = self._embed_text(content, provider)
        faiss_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
        bm25_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)

        all_dense_hits: list[IMessageJobContextHit] = []
        all_sparse_hits: list[IMessageJobContextHit] = []


        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(valid_documents) or 1, 10)) as executor:
            # Ném việc cho công nhân
            futures = [
                executor.submit(self._search_single_document, doc, query_embedding, content, faiss_store, bm25_store)
                for doc in valid_documents
            ]
            
            # Thu hoạch kết quả ngay khi công nhân làm xong
            for future in concurrent.futures.as_completed(futures):
                dense_res, sparse_res = future.result()
                all_dense_hits.extend(dense_res)
                all_sparse_hits.extend(sparse_res)

        all_dense_hits.sort(key=lambda item: item.score, reverse=True)
        all_sparse_hits.sort(key=lambda item: item.score, reverse=True)

        if all_dense_hits or all_sparse_hits:
            self.logger.info(f"Fusing {len(all_dense_hits)} Dense and {len(all_sparse_hits)} Sparse hits", file_caller=self._retrieve_context_hits.__name__)
            return self.hybrid_search_service.fuse_results(all_dense_hits, all_sparse_hits, top_k=5)

        return self._keyword_context_hits(content, self._get_attached_document_texts(conversation))
    
    def _embed_text(self, text: str, provider: EProviderName) -> np.ndarray:
        llm_client = self.llm_provider_factory.get_provider(provider)
        model_name = self._get_embedding_model(provider)
        response = llm_client.embedding(ICompletionRequest(provider=provider, model=model_name, prompt=text))
        return response.embedding.astype(np.float32)

    def _load_document_chunk_metadata(self, document_id: str) -> dict | None:
        cache_key = f"document_chunks:{document_id}:meta"
        # Ghi log file_caller cho Cache Service
        cache_service = self.cache_session.connect(file_caller=self._load_document_chunk_metadata.__name__)
        try:
            return cache_service.get(cache_key, file_caller=self._load_document_chunk_metadata.__name__)
        finally:
            self.cache_session.disconnect(file_caller=self._load_document_chunk_metadata.__name__)

    def _resolve_chunk_text(self, document_id: str, vector_id: int, metadata: dict) -> str:
        """Giải mã ID int64 ngược về chuỗi chunk_key ban đầu để lấy Text."""
        chunk_key = self._vector_id_to_chunk_key(document_id, vector_id)
        chunks = metadata.get("chunks", {})
        if chunk_key not in chunks:
            raise ValueError(f"Chunk not found for key {chunk_key}")
        return chunks[chunk_key]

    def _vector_id_to_chunk_key(self, document_id: str, vector_id: int) -> str:
        """Thuật toán giải mã mảng IDs được hash lúc UploadJob."""
        base_hash = hashlib.sha256(document_id.encode("utf-8")).digest()[:8]
        base_id = int.from_bytes(base_hash, "big") & 0x7FFFFFFFFFFFFFFF
        chunk_index = int(vector_id) - base_id - 1
        if chunk_index < 0:
            raise ValueError(f"Invalid vector id {vector_id} for document {document_id}")
        return f"{document_id}:{chunk_index + 1}"

    def _get_embedding_model(self, provider: EProviderName) -> str:
        for provider_record in self.config_provider.get_list_providers():
            if provider_record.provider_name == provider:
                return provider_record.embed_model_name
        raise ValueError(f"Embedding model not configured for provider {provider}")

    def _keyword_context_hits(self, content: str, document_texts: list[str]) -> list[IMessageJobContextHit]:
        query_words = set(content.lower().split())
        scored_paragraphs: list[tuple[int, str]] = []
        
        # Duyệt qua Generator, không tạo mảng khổng lồ trong RAM
        for paragraph in self._generate_paragraphs(document_texts):
            paragraph_words = set(paragraph.lower().split())
            score = len(query_words.intersection(paragraph_words))
            if score > 0:
                scored_paragraphs.append((score, paragraph))

        scored_paragraphs.sort(key=lambda item: item[0], reverse=True)
        return [
            IMessageJobContextHit(text=paragraph[:200] + "...", score=float(score), source_document_id=None)
            for score, paragraph in scored_paragraphs[:5]
        ]

    def _get_attached_document_texts(self, conversation: ConversationModel) -> list[str]:
        """
        Thu thập toàn bộ nội dung văn bản thô của các tài liệu đính kèm phục vụ luồng fallback keyword match.
        Sử dụng extract_service chuẩn IoC khi Redis cache bị mất hoặc hết hạn dữ liệu (Eviction).
        """
        document_texts: list[str] = []
        
        # Tìm tất cả các liên kết file với Conversation hiện tại
        mappings = ConversationFilesModel.objects.filter(conversation=conversation)
        
        for mapping in mappings:
            document = mapping.faiss_index
            if document is None or document.status != "indexed":
                continue
                
            doc_id_str = str(document.faiss_index_id)
            
            # Thử tải dữ liệu chunks từ Redis cache trước để tối ưu tốc độ RAM
            meta = self._load_document_chunk_metadata(doc_id_str)
            if meta and "chunks" in meta:
                chunks_dict = meta["chunks"]
                # Sắp xếp các phân đoạn theo thứ tự index tăng dần (doc_id:1, doc_id:2...) để văn bản liền mạch
                sorted_keys = sorted(chunks_dict.keys(), key=lambda k: int(k.split(":")[-1]) if ":" in k else 0)
                full_text = "\n".join(chunks_dict[k] for k in sorted_keys)
                document_texts.append(full_text)
                continue
                
            # FALLBACK: Nếu Redis trống, sử dụng đúng self.extract_service để bóc tách lại file vật lý từ ổ cứng
            if document.file_path:
                file_path = Path(document.file_path)
                if file_path.exists():
                    try:
                        # Tiến hành trích xuất sử dụng đúng service đã được inject qua Container
                        raw_texts = self.extract_service.extract(file_path, EProviderName.MISTRAL)
                        if raw_texts and raw_texts.extracted_text:
                            document_texts.append(raw_texts.extracted_text)
                            self.logger.info(f"Fallback text extraction successful for document {doc_id_str}", source=str(self.__class__))
                    except Exception as exc:
                        self.logger.error(
                            f"Fallback text extraction failed for document {doc_id_str}: {exc}",
                            source=str(self.__class__),
                            method_call=self._get_attached_document_texts.__name__
                        )
                        
        return document_texts
    
    def _retrieve_graph_context(self, content: str, conversation: ConversationModel, provider: EProviderName) -> str:
        try:
            mappings = ConversationFilesModel.objects.filter(conversation=conversation)
            if not mappings.exists():
                return ""
            
            doc_uuid_list = list(mappings.values_list("faiss_index__faiss_index_id", flat=True))
            safe_ids_str = "_".join(str(uid).replace("-", "") for uid in doc_uuid_list)
            index_name = f"graph_index_{safe_ids_str}"

            llm_client = self.llm_provider_factory.get_provider(provider)

            retriever = self.neo4j_service.create_graph_retriever( 
                template="MATCH (c:Chunk)-[:MENTIONS]->(e) WHERE c.id = $chunk_id RETURN e.id",
                embedder=llm_client,
                index_name=index_name,
                file_caller=self._retrieve_graph_context.__name__
            )

            graph_answer = self.neo4j_service.search(
                query_text=content,
                limit=5,
                llm=llm_client,
                retriever=retriever,
                template=RagTemplate(),
                file_caller=self._retrieve_graph_context.__name__
            )
        
            return graph_answer
        
        except Exception as e:
            self.logger.error(f"Lỗi khi truy vấn Graph RAG: {e}")
            return ""

    def _build_prompt(self, content: str, context_hits: list[dict], graph_context: str) -> str:
        context_text = "\n".join(hit["text"] for hit in context_hits)
        system_prompt = "You are an intelligent assistant. Answer the user based on the provided text context and graph relationships."
        return f"System prompt: {system_prompt}\n\nContext from documents:\n{context_text}\n\nGraph Context:\n{graph_context}\n\nUser: {content}\n\nAssistant:"
    
    def _resolve_chunk_text(self, document_id: str, vector_id: int, metadata: dict, base_id: int) -> str:
        """Đã Tuning: Nhận thẳng base_id, không gọi hashlib nữa."""
        chunk_key = self._vector_id_to_chunk_key(document_id, vector_id, base_id)
        chunks = metadata.get("chunks", {})
        if chunk_key not in chunks:
            raise ValueError(f"Chunk not found for key {chunk_key}")
        return chunks[chunk_key]

    def _vector_id_to_chunk_key(self, document_id: str, vector_id: int, base_id: int) -> str:
        """Đã Tuning: Tính toán siêu nhẹ vì base_id đã được tính sẵn 1 lần ở ngoài."""
        chunk_index = int(vector_id) - base_id - 1
        if chunk_index < 0:
            raise ValueError(f"Invalid vector id {vector_id} for document {document_id}")
        return f"{document_id}:{chunk_index + 1}"
    
    def _search_single_document(self, document, query_embedding, content: str, faiss_store, bm25_store) -> tuple[list[IMessageJobContextHit], list[IMessageJobContextHit]]:
        """Hàm công nhân: Chịu trách nhiệm tìm kiếm trên 1 file duy nhất."""
        dense_hits: list[IMessageJobContextHit] = []
        sparse_hits: list[IMessageJobContextHit] = []
        
        doc_id_str = str(document.faiss_index_id)
        meta = self._load_document_chunk_metadata(doc_id_str)
        if meta is None:
            return [], []

        # Tính Hash đúng 1 lần cho cả 1 file
        base_hash = hashlib.sha256(doc_id_str.encode("utf-8")).digest()[:8]
        base_id = int.from_bytes(base_hash, "big") & 0x7FFFFFFFFFFFFFFF

        # FAISS SEARCH
        load_faiss = faiss_store.load(doc_id_str, file_caller=self._search_single_document.__name__)
        if load_faiss.is_success and load_faiss.index is not None:
            query_res = faiss_store.search(load_faiss.index, doc_id_str, query_embedding, limit=5, file_caller=self._search_single_document.__name__)
            for distance, vector_id in zip(query_res.distances, query_res.indices):
                try:
                    # Truyền base_id đã tính ở trên xuống
                    chunk_text = self._resolve_chunk_text(doc_id_str, vector_id, meta, base_id)
                    similarity = 1.0 / (1.0 + float(distance))
                    dense_hits.append(IMessageJobContextHit(text=chunk_text, score=similarity, source_document_id=doc_id_str))
                except ValueError:
                    continue

        # BM25 SEARCH
        load_bm25 = bm25_store.load(doc_id_str, file_caller=self._search_single_document.__name__)
        if load_bm25.is_success and load_bm25.index is not None:
            bm25_res = bm25_store.search(load_bm25.index, doc_id_str, query_vector=np.array([]), query_text=content, limit=5, file_caller=self._search_single_document.__name__)
            for score, chunk_key in zip(bm25_res.distances, bm25_res.indices):
                try:
                    chunk_text = meta.get("chunks", {}).get(str(chunk_key))
                    if chunk_text:
                        sparse_hits.append(IMessageJobContextHit(text=chunk_text, score=float(score), source_document_id=doc_id_str))
                except Exception:
                    continue


        return dense_hits, sparse_hits
    
    def _generate_paragraphs(self, document_texts: list[str]):
        """
        TỐI ƯU RAM (Bài toán 2): Hàm Generator vắt từng dòng văn bản.
        Sinh ra đoạn nào xử lý đoạn đó, rác sẽ được dọn ngay khỏi RAM.
        """
        for doc_text in document_texts:
            for p in doc_text.split("\n"):
                clean_p = p.strip()
                if clean_p:
                    yield clean_p