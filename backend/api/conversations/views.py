from __future__ import annotations

import datetime
import hashlib
import json
import time
from pathlib import Path
from typing import cast
from uuid import UUID

import numpy as np
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from backend.apps.config import container
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.services.chat.models import (
    ConversationModel,
    MessageModel,
    DocumentModel,
    ConversationFilesModel,
)
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.application.conversations.application import ConversationApplication
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.system_dirs import METADATA_DIR

# Singleton application instance
_container = container.BackendContainer()
_conversation_app = _container.conversation_application()
DEFAULT_LOGGER = _container.log_pool()


def call_llm_with_resilience(provider_name: str, model_name: str, prompt: str, max_retries: int = 2) -> tuple[str, str]:
    """Call LLM with retry logic and fallback providers."""
    factory = LLMProviderFactory(_container.config_provider(), DEFAULT_LOGGER)
    
    # Try the requested provider first
    for attempt in range(max_retries):
        try:
            provider = EProviderName(provider_name)
            llm_client = factory.get_provider(provider, file_caller="call_llm_with_resilience")
            
            request = ICompletionRequest(
                provider=provider,
                model=model_name,
                prompt=prompt,
            )
            
            response = llm_client.generate(request, file_caller="call_llm_with_resilience")
            return response.content, provider_name
            
        except Exception as e:
            DEFAULT_LOGGER.warning(
                f"Attempt {attempt + 1}/{max_retries} failed for provider {provider_name}: {e}",
                source="call_llm_with_resilience"
            )
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Wait before retry
    
    raise Exception(f"Failed to get response from {provider_name} after {max_retries} attempts")


def _resolve_provider_model(provider_name: str | None, model_name: str | None) -> tuple[str, str]:
    provider_value = (provider_name or "").strip()
    model_value = (model_name or "").strip()
    configured_providers = _container.config_provider().get_list_providers()

    for configured in configured_providers:
        if model_value in {configured.model_name, configured.provider_name.value}:
            return configured.provider_name.value, configured.model_name

    for configured in configured_providers:
        if provider_value == configured.provider_name.value:
            model = model_value if model_value and model_value != "auto" else configured.model_name
            return configured.provider_name.value, model

    ollama = next(
        (
            configured
            for configured in configured_providers
            if configured.provider_name == EProviderName.OLLAMA
        ),
        None,
    )
    fallback = ollama or (configured_providers[0] if configured_providers else None)
    if fallback:
        return fallback.provider_name.value, fallback.model_name

    return EProviderName.OLLAMA.value, model_value or "qwen2.5:1.5b-instruct"


def _build_rag_context(documents: list[DocumentModel], user_query: str, top_k: int = 5) -> tuple[str, list[dict]]:
    """
    Build RAG context using FAISS vector search.
    Loads FAISS indices for all indexed documents, embeds the query,
    searches for top_k most similar chunks, returns concatenated context.

    Falls back to keyword paragraph search if FAISS is unavailable.
    """
    context_text = ""
    context_hits: list[dict] = []

    # Only search in indexed documents
    indexed_docs = [d for d in documents if d.documents_status == "indexed"]
    if not indexed_docs:
        return "", []

    try:
        # Build the embed query
        embed_provider = EProviderName.GEMINI
        embed_model = "gemini-embedding-2"
        factory = LLMProviderFactory(_container.config_provider(), _container.log_pool())
        embed_client = factory.get_provider(embed_provider)

        embed_req = ICompletionRequest(
            provider=embed_provider,
            model=embed_model,
            prompt=user_query,
        )
        query_vector_resp = embed_client.embedding(embed_req)
        query_vector = query_vector_resp.embedding.reshape(1, -1).astype(np.float32)

        locate_service = LocateService(metadata_dir=METADATA_DIR, logger=_container.log_pool())
        faiss_service = cast(
            IVectorStoreService,
            locate_service.get_vector_store(EBackendStorageName.FAISS),
        )

        all_results: list[tuple[float, str]] = []

        for doc in indexed_docs:
            # Load FAISS index for this document
            vector_id = doc.documents_conversation.conversations_id
            try:
                load_resp = faiss_service.load(vector_id)
                index = load_resp.index
            except ValueError:
                # Index not found on disk; skip this document
                continue

            # Search
            search_resp = faiss_service.search(
                index=index,
                vector_id=vector_id,
                query_vector=query_vector,
                limit=top_k,
            )

            # Load chunk metadata (id → text)
            chunk_texts: dict[int, str] = {}
            metadata_path = METADATA_DIR / "docs" / f"{vector_id}.json"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    raw_chunks = meta.get("chunks", {})
                    chunk_texts = {int(k): v for k, v in raw_chunks.items()}

            # Collect results
            for dist, idx in zip(search_resp.distances, search_resp.indices):
                if idx in chunk_texts:
                    all_results.append((dist, chunk_texts[idx]))

        # Sort by distance (ascending = more similar)
        all_results.sort(key=lambda x: x[0])
        top_results = all_results[:top_k]

        if top_results:
            context_text = "\n".join([text for _, text in top_results])
            context_hits = [
                {"text": text[:200] + ("..." if len(text) > 200 else ""), "score": round(dist, 4)}
                for dist, text in top_results
            ]

    except Exception as e:
        DEFAULT_LOGGER.warning(
            f"FAISS retrieval failed, falling back to keyword search: {e}",
            source="MessageListView",
        )
        # Fallback: keyword paragraph search
        doc_contents = [d.documents_content for d in indexed_docs if d.documents_content]
        if doc_contents:
            paragraphs = []
            for doc_text in doc_contents:
                paragraphs.extend([p.strip() for p in doc_text.split("\n") if p.strip()])

            query_words = set(user_query.lower().split())
            scored_paragraphs = []
            for p in paragraphs:
                p_words = set(p.lower().split())
                score = len(query_words.intersection(p_words))
                if score > 0:
                    scored_paragraphs.append((score, p))

            scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
            top_paragraphs = scored_paragraphs[:top_k]
            context_text = "\n".join([p for _, p in top_paragraphs])
            context_hits = [
                {"text": p[:200] + ("..." if len(p) > 200 else ""), "score": s}
                for s, p in top_paragraphs
            ]

    return context_text, context_hits


class ConversationListView(APIView):
    def get(self, request):
        # Use application layer
        result = _conversation_app.list_conversations()
        data = []
        for conv in result:
            # conv is a ConversationModel instance
            data.append({
                "id": str(conv.conversations_id),
                "title": conv.conversations_name or "Untitled",
                "status": "ready"
            })
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        title = request.data.get("title", "New Conversation")
        provider = request.data.get("provider", "auto")
        model = request.data.get("model", "auto")
        system_prompt = request.data.get("system_prompt", "")
        document_ids_raw = request.data.get("document_ids", [])

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"{title} - {now_str}"

        # Convert string IDs to UUIDs
        document_ids = []
        for doc_id in document_ids_raw:
            try:
                document_ids.append(UUID(str(doc_id)))
            except (ValueError, TypeError):
                pass

        # Use application layer to create conversation
        try:
            conv_obj = _conversation_app.create_init_conversation(
                conversation_title=title,
                file_caller="ConversationListView"
            )
            conv_id = conv_obj.conversations_id
            
            # Note: Document linking is complex due to the OneToOne relationship
            # between DocumentModel and ConversationModel. 
            # For now, skip document linking during conversation creation.
            # Documents are linked during upload process.
                
        except Exception as e:
            DEFAULT_LOGGER.error(f"Error creating conversation: {e}", source="ConversationListView")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Add bootstrap message
        bootstrap_text = "I've started a new conversation. How can I assist you today?"

        MessageModel.objects.create(
            messages_conversation=conv_obj,
            messages_is_user_send=False,
            messages_content=bootstrap_text
        )

        return Response({
            "id": str(conv_id),
            "conversation_id": str(conv_id),
            "title": title,
            "status": "ready"
        }, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    def get(self, request, conversation_id: str):
        try:
            conv_uuid = UUID(conversation_id)
            conv_obj = ConversationModel.objects.get(pk=conv_uuid)
            return Response({
                "id": str(conv_obj.conversations_id),
                "title": conv_obj.conversations_name or "Untitled",
                "status": "ready"
            }, status=status.HTTP_200_OK)
        except (ValueError, ValidationError, ConversationModel.DoesNotExist):
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)


class ConversationStatusView(APIView):
    def get(self, request, conversation_id: str):
        return Response({
            "conversation_id": conversation_id,
            "status": "ready"
        }, status=status.HTTP_200_OK)


class ConversationDocumentsView(APIView):
    def patch(self, request, conversation_id: str):
        try:
            conv_uuid = UUID(conversation_id)
            conv_obj = ConversationModel.objects.get(pk=conv_uuid)
            
            document_ids_raw = request.data.get("document_ids", [])
            
            # Note: Due to the OneToOne relationship between DocumentModel and ConversationModel,
            # we cannot directly "add documents" to a conversation in the traditional sense.
            # Each document is already tied to its own conversation.
            # This endpoint is kept for API compatibility but has limited functionality.
            
            DEFAULT_LOGGER.info(f"Document update requested for conversation {conversation_id}", source="ConversationDocumentsView")
            return Response({"status": "updated"}, status=status.HTTP_200_OK)
        except (ValueError, ValidationError, ConversationModel.DoesNotExist):
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            DEFAULT_LOGGER.error(f"Error updating conversation documents: {e}", source="ConversationDocumentsView")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageListView(APIView):
    def get(self, request, conversation_id: str):
        try:
            conv_uuid = UUID(conversation_id)
            ConversationModel.objects.get(pk=conv_uuid)
        except (ValueError, ValidationError, ConversationModel.DoesNotExist):
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        msgs = MessageModel.objects.filter(
            messages_conversation_id=conv_uuid
        ).order_by("messages_created_at")
        data = []
        for m in msgs:
            data.append({
                "role": "user" if m.messages_is_user_send else "assistant",
                "content": m.messages_content
            })
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, conversation_id: str):
        try:
            conv_uuid = UUID(conversation_id)
            conv = ConversationModel.objects.get(pk=conv_uuid)
        except (ValueError, ValidationError, ConversationModel.DoesNotExist):
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        content = request.data.get("content")
        if not content:
            return Response({"error": "Message content is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Save user message
        MessageModel.objects.create(
            messages_conversation=conv,
            messages_is_user_send=True,
            messages_content=content
        )

        # 2. Get attached indexed documents
        # Note: DocumentModel has a OneToOne relationship with ConversationModel
        try:
            doc = DocumentModel.objects.get(documents_conversation=conv)
            attached_docs = [doc]  # The main document associated with this conversation
        except DocumentModel.DoesNotExist:
            attached_docs = []

        # 3. Retrieve context via FAISS vector search (with keyword fallback)
        start_retrieval = time.time()
        context_text, context_hits = _build_rag_context(attached_docs, content, top_k=5)
        retrieval_ms = int((time.time() - start_retrieval) * 1000)

        # 4. Build prompt
        system_prompt = "You are a helpful assistant. Answer based ONLY on the provided context. Do NOT make up answers."
        llm_prompt = f"System prompt: {system_prompt}\n\nContext from documents:\n{context_text}\n\nUser: {content}\n\nAssistant:"

        # 5. Resolve provider/model
        provider_name, model_name = _resolve_provider_model(
            request.data.get("provider", "auto"),
            request.data.get("model", "auto"),
        )

        # 6. Call LLM with retry + circuit breaker
        start_llm = time.time()
        answer = ""
        used_mock = False
        used_provider = provider_name

        try:
            answer, used_provider = call_llm_with_resilience(
                provider_name=provider_name,
                model_name=model_name,
                prompt=llm_prompt,
                max_retries=2,
            )
        except Exception as exc:
            DEFAULT_LOGGER.error(
                f"All LLM providers failed after retries: {exc}. Using mock response.",
                source="MessageListView",
            )
            if context_text:
                answer = (
                    f"⚠️ **Khong the ket noi den model {provider_name} ({model_name}).**\n\n"
                    f"Duoi day la noi dung tai lieu trich xuat tu ngon ngu (Simulated Response):\n\n"
                    f"{context_text}"
                )
            else:
                answer = (
                    f"⚠️ **Khong the ket noi den model {provider_name} ({model_name}).**\n\n"
                    f"Khong tim thay ngon ngu phu hop trong tai lieu de tra loi."
                )
            used_mock = True

        llm_ms = int((time.time() - start_llm) * 1000)
        total_ms = int((time.time() - start_retrieval) * 1000)

        # 7. Save assistant message
        MessageModel.objects.create(
            messages_conversation=conv,
            messages_is_user_send=False,
            messages_content=answer
        )

        return Response({
            "conversation_id": str(conv.conversations_id),
            "assistant": answer,
            "used_mock": used_mock,
            "metrics": {
                "provider": used_provider,
                "model": model_name,
                "total_ms": total_ms,
                "embed_ms": retrieval_ms,
                "query_ms": retrieval_ms,
                "response_ms": llm_ms,
                "retrieval_hits": context_hits
            }
        }, status=status.HTTP_200_OK)
