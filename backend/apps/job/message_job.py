import hashlib
import time
from pathlib import Path
from typing import List
import numpy as np

from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService
from backend.apps.interfaces.job.i_message_job import IMessageJob, MessageResponse, ContextHit
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.cache.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, MessageModel

class MessageJob(IMessageJob):
    def __init__(self, llm_provider_factory: ILLMProviderFactory, config_provider: IConfigProvider, locate_service: ILocateService, cache_session: IConnectCacheSession, logger: ILogger, hybrid_search_service: IHybridSearchService, extract_service: IExtractContent):
        self.llm_provider_factory = llm_provider_factory
        self.config_provider = config_provider
        self.locate_service = locate_service
        self.cache_session = cache_session
        self.logger = logger,
        self.hybrid_search_service = hybrid_search_service,
        self.extract_service = extract_service

    def run(self, conversation_id: str, content: str, provider: EProviderName, model_name: str | None = None) -> MessageResponse:
        conversation = self._get_conversation(conversation_id)
        self._save_message(conversation, is_user_send=True, content=content)

        context_hits = self._retrieve_context_hits(content, conversation, provider)
        context_hits_dicts = [{"text": hit.text, "score": hit.score} for hit in context_hits]
        prompt = self._build_prompt(content, context_hits_dicts)

        model = model_name or "gemini-2.5-flash"
        llm_client = self.llm_provider_factory.get_provider(provider)

        self.logger.info(
            f"Generating assistant response for conversation={conversation_id} provider={provider.value}",
            source=str(self.__class__),
            method_call=self.run.__name__,
        )

        start_time = time.time()
        response = llm_client.generate(ICompletionRequest(provider=provider, model=model, prompt=prompt, context_hits=context_hits_dicts))
        latency_ms = int((time.time() - start_time) * 1000)

        self._save_message(conversation, is_user_send=False, content=response)

        return MessageResponse(
            conversation_id=str(conversation.conversation_id),
            assistant=response,
            provider=provider.value,
            model=model,
            latency_ms=latency_ms,
            retrieval_hits=context_hits
        )

    def _get_conversation(self, conversation_id: str) -> ConversationModel:
        try:
            return ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist as exc:
            raise ValueError(f"Conversation not found: {conversation_id}") from exc

    def _save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        return MessageModel.objects.create(message_conversation=conversation, message_is_user_send=is_user_send, message_content=content)

    def _retrieve_context_hits(self, content: str, conversation: ConversationModel, provider: EProviderName) -> List[ContextHit]:
        query_embedding = self._embed_text(content, provider)
        
        dense_hits: List[ContextHit] = []
        sparse_hits: List[ContextHit] = []
        
        faiss_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
        bm25_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)

        mappings = ConversationFilesModel.objects.filter(conversation=conversation)
        for mapping in mappings:
            document = mapping.faiss_index
            if document is None or document.status != "indexed":
                continue

            doc_id_str = str(document.faiss_index_id)
            meta = self._load_document_chunk_metadata(doc_id_str)
            if meta is None:
                continue

            # FAISS SEARCH (Tìm theo Ngữ Nghĩa/semantic search)
            load_faiss = faiss_store.load(doc_id_str, file_caller=self._retrieve_context_hits.__name__)
            if load_faiss.is_success and load_faiss.index is not None:
                query_res = faiss_store.search(
                    load_faiss.index, doc_id_str, query_embedding, limit=5, file_caller=self._retrieve_context_hits.__name__
                )
                for distance, vector_id in zip(query_res.distances, query_res.indices):
                    try:
                        chunk_text = self._resolve_chunk_text(doc_id_str, vector_id, meta)
                        similarity = 1.0 / (1.0 + float(distance))
                        dense_hits.append(ContextHit(text=chunk_text, score=similarity, source_document_id=doc_id_str))
                    except ValueError:
                        continue

            # BM25 SEARCH (Tìm theo Từ Khóa/ keyword search)
            load_bm25 = bm25_store.load(doc_id_str, file_caller=self._retrieve_context_hits.__name__)
            if load_bm25.is_success and load_bm25.index is not None:
                bm25_res = bm25_store.search(
                    load_bm25.index, doc_id_str, query_vector=np.array([]), query_text=content, limit=5, file_caller=self._retrieve_context_hits.__name__
                )
                for score, chunk_key in zip(bm25_res.distances, bm25_res.indices):
                    try:
                        # BM25 trả về trực tiếp string key "doc_id:chunk_idx"
                        chunk_text = meta.get("chunks", {}).get(str(chunk_key))
                        if chunk_text:
                            sparse_hits.append(ContextHit(text=chunk_text, score=float(score), source_document_id=doc_id_str))
                    except Exception:
                        continue

        # Sắp xếp cục bộ trước khi truyền vào RRF để lấy Rank
        dense_hits.sort(key=lambda item: item.score, reverse=True)
        sparse_hits.sort(key=lambda item: item.score, reverse=True)

        # HYBRID FUSION (Gộp kết quả bằng RRF)
        if dense_hits or sparse_hits:
            self.logger.info("Fusing Dense and Sparse results using RRF", file_caller=self._retrieve_context_hits.__name__)
            return self.hybrid_search_service.fuse_results(dense_hits, sparse_hits, top_k=5)

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

    def _keyword_context_hits(self, content: str, document_texts: List[str]) -> List[ContextHit]:
        paragraphs: List[str] = []
        for doc_text in document_texts:
            paragraphs.extend([p.strip() for p in doc_text.split("\n") if p.strip()])

        query_words = set(content.lower().split())
        scored_paragraphs: List[tuple[int, str]] = []
        for paragraph in paragraphs:
            paragraph_words = set(paragraph.lower().split())
            score = len(query_words.intersection(paragraph_words))
            if score > 0:
                scored_paragraphs.append((score, paragraph))

        scored_paragraphs.sort(key=lambda item: item[0], reverse=True)
        return [
            ContextHit(text=paragraph[:200] + "...", score=float(score), source_document_id=None)
            for score, paragraph in scored_paragraphs[:5]
        ]

    def _get_attached_document_texts(self, conversation: ConversationModel) -> List[str]:
        """
        Thu thập toàn bộ nội dung văn bản thô của các tài liệu đính kèm phục vụ luồng fallback keyword match.
        Sử dụng extract_service chuẩn IoC khi Redis cache bị mất hoặc hết hạn dữ liệu (Eviction).
        """
        document_texts: List[str] = []
        
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
                        raw_text = self.extract_service.extract_from_file_text(file_path, EProviderName.MISTRAL)
                        if raw_text:
                            document_texts.append(raw_text)
                    except Exception as exc:
                        self.logger.error(
                            f"Fallback text extraction failed for document {doc_id_str}: {exc}",
                            source=str(self.__class__),
                            method_call=self._get_attached_document_texts.__name__
                        )
                        
        return document_texts

    def _build_prompt(self, content: str, context_hits: List[dict]) -> str:
        context_text = "\n".join(hit["text"] for hit in context_hits)
        system_prompt = "You are a helpful assistant."
        return f"System prompt: {system_prompt}\n\nContext from documents:\n{context_text}\n\nUser: {content}\n\nAssistant:"