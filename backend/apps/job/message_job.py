import hashlib
import time
from pathlib import Path
from typing import List

import numpy as np

from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.cache.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, MessageModel


class MessageJob:
    """Orchestrates chat message processing for a conversation."""

    def __init__(
        self,
        llm_provider_factory: ILLMProviderFactory,
        config_provider: IConfigProvider,
        locate_service: ILocateService,
        cache_session: IConnectCacheSession,
        logger: ILogger,
    ):
        self.llm_provider_factory = llm_provider_factory
        self.config_provider = config_provider
        self.locate_service = locate_service
        self.cache_session = cache_session
        self.logger = logger

    def run(
        self,
        conversation_id: str,
        content: str,
        provider: EProviderName,
        model_name: str | None = None,
    ) -> dict:
        conversation = self._get_conversation(conversation_id)
        self._save_message(conversation, is_user_send=True, content=content)

        context_hits = self._retrieve_context_hits(content, conversation, provider)
        prompt = self._build_prompt(content, context_hits)

        model = model_name or "gemini-2.5-flash"
        llm_client = self.llm_provider_factory.get_provider(provider)

        self.logger.info(
            f"Generating assistant response for conversation={conversation_id} provider={provider}",
            source=str(self.__class__),
            method_call=self.run.__name__,
        )

        start_time = time.time()
        answer = llm_client.generate(
            ICompletionRequest(
                provider=provider,
                model=model,
                prompt=prompt,
                context_hits=context_hits,
            )
        )
        latency_ms = int((time.time() - start_time) * 1000)

        self._save_message(conversation, is_user_send=False, content=answer)

        return {
            "conversation_id": str(conversation.conversation_id),
            "assistant": answer,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "retrieval_hits": context_hits,
        }

    def _get_conversation(self, conversation_id: str) -> ConversationModel:
        try:
            return ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist as exc:
            raise ValueError(f"Conversation not found: {conversation_id}") from exc

    def _save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        return MessageModel.objects.create(
            message_conversation=conversation,
            message_is_user_send=is_user_send,
            message_content=content,
        )

    def _retrieve_context_hits(
        self,
        content: str,
        conversation: ConversationModel,
        provider: EProviderName,
    ) -> List[dict]:
        query_embedding = self._embed_text(content, provider)
        hits: List[dict] = []
        vector_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)

        mappings = ConversationFilesModel.objects.filter(conversation=conversation)
        for mapping in mappings:
            document = mapping.faiss_index
            if document is None or document.status != "indexed":
                continue

            meta = self._load_document_chunk_metadata(str(document.faiss_index_id))
            if meta is None:
                continue

            load_response = vector_store.load(str(document.faiss_index_id), file_caller=self._retrieve_context_hits.__name__)
            if not load_response.is_success or load_response.index is None:
                continue

            query_response = vector_store.search(
                load_response.index,
                str(document.faiss_index_id),
                query_embedding,
                limit=5,
                file_caller=self._retrieve_context_hits.__name__,
            )

            for distance, vector_id in zip(query_response.distances, query_response.indices):
                try:
                    chunk_text = self._resolve_chunk_text(str(document.faiss_index_id), vector_id, meta)
                except ValueError:
                    continue
                similarity = 1.0 / (1.0 + float(distance))
                hits.append(
                    {
                        "text": chunk_text[:200] + "...",
                        "score": similarity,
                        "source_document_id": str(document.faiss_index_id),
                    }
                )

        hits.sort(key=lambda item: item["score"], reverse=True)
        if hits:
            return hits[:5]

        return self._keyword_context_hits(content, self._get_attached_document_texts(conversation))

    def _embed_text(self, text: str, provider: EProviderName) -> np.ndarray:
        llm_client = self.llm_provider_factory.get_provider(provider)
        model_name = self._get_embedding_model(provider)
        response = llm_client.embedding(
            ICompletionRequest(provider=provider, model=model_name, prompt=text)
        )
        return response.embedding.astype(np.float32)

    def _load_document_chunk_metadata(self, document_id: str) -> dict | None:
        cache_key = f"document_chunks:{document_id}:meta"
        cache_service = self.cache_session.connect(file_caller=self._load_document_chunk_metadata.__name__)
        try:
            return cache_service.get(cache_key, file_caller=self._load_document_chunk_metadata.__name__)
        finally:
            self.cache_session.disconnect(file_caller=self._load_document_chunk_metadata.__name__)

    def _resolve_chunk_text(self, document_id: str, vector_id: int, metadata: dict) -> str:
        chunk_key = self._vector_id_to_chunk_key(document_id, vector_id)
        chunks = metadata.get("chunks", {})
        if chunk_key not in chunks:
            raise ValueError(f"Chunk not found for key {chunk_key}")
        return chunks[chunk_key]

    def _vector_id_to_chunk_key(self, document_id: str, vector_id: int) -> str:
        base_hash = hashlib.sha256(document_id.encode("utf-8")).digest()[:8]
        base_id = int.from_bytes(base_hash, "big") & 0x7FFFFFFFFFFFFFFF
        chunk_index = int(vector_id) - base_id - 1
        if chunk_index < 0:
            raise ValueError(f"Invalid vector id {vector_id} for document {document_id}")
        return f"{document_id}:{chunk_index + 1}"

    def _get_embedding_model(self, provider: EProviderName) -> str:
        providers = self.config_provider.get_list_providers()
        for provider_record in providers:
            if provider_record.provider_name == provider:
                return provider_record.embed_model_name
        raise ValueError(f"Embedding model not configured for provider {provider}")

    def _keyword_context_hits(self, content: str, document_texts: List[str]) -> List[dict]:
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
            {"text": paragraph[:200] + "...", "score": score}
            for score, paragraph in scored_paragraphs[:5]
        ]

    def _build_prompt(self, content: str, context_hits: List[dict]) -> str:
        context_text = "\n".join(hit["text"] for hit in context_hits)
        system_prompt = "You are a helpful assistant."
        return (
            f"System prompt: {system_prompt}\n\n"
            f"Context from documents:\n{context_text}\n\n"
            f"User: {content}\n\nAssistant:"
        )
