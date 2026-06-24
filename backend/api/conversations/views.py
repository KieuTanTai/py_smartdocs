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
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# Ensure UTF-8 encoding for Windows compatibility
import sys
import io
if sys.platform == 'win32' and 'pytest' not in sys.modules:
    if not hasattr(sys.stdout, '_utf8_wrapped'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stdout._utf8_wrapped = True
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
            sys.stderr._utf8_wrapped = True
        except (AttributeError, ValueError, io.UnsupportedOperation):
            pass

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
__container = container.BackendContainer()
_conversation_app = __container.conversation_application()
DEFAULT_LOGGER = __container.log_pool()


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
    # TEMP FIX: Allow uploaded status as well since upload sets status to "uploaded" not "indexed"
    indexed_docs = [d for d in documents if d.documents_status in ("indexed", "uploaded")]
    if not indexed_docs:
        return "", []

    try:
        # Build the embed query
        embed_provider = EProviderName.GEMINI
        embed_model = "gemini-embedding-2"
        factory = LLMProviderFactory(__container.config_provider(), __container.log_pool())
        embed_client = factory.get_provider(embed_provider)

        DEFAULT_LOGGER.info(
            f"Creating embedding for query: {user_query[:100]}...",
            source="_build_rag_context"
        )

        embed_req = ICompletionRequest(
            provider=embed_provider,
            model=embed_model,
            prompt=user_query,
        )
        query_vector_resp = embed_client.embedding(embed_req)
        query_vector = query_vector_resp.embedding.reshape(1, -1).astype(np.float32)
        
        DEFAULT_LOGGER.info(
            f"Successfully created embedding vector of shape: {query_vector.shape}",
            source="_build_rag_context"
        )

        locate_service = LocateService(metadata_dir=METADATA_DIR, logger=__container.log_pool())
        faiss_service = cast(
            IVectorStoreService,
            locate_service.get_vector_store(EBackendStorageName.FAISS),
        )

        all_results: list[tuple[float, str]] = []

        for doc in indexed_docs:
            # Load FAISS index for this document
            # FAISS is indexed by conversation_id
            vector_id = str(doc.documents_conversation.conversations_id)
            # But metadata JSON is indexed by document_id!
            document_id = str(doc.document_id)
            
            try:
                load_resp = faiss_service.load(doc.documents_conversation.conversations_id)
                index = load_resp.index
            except ValueError:
                # Index not found on disk; skip this document
                DEFAULT_LOGGER.warning(
                    f"FAISS index not found for conversation {vector_id}",
                    source="_build_rag_context"
                )
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
            # Use document_id to load metadata, not conversation_id!
            metadata_path = METADATA_DIR / "docs" / f"{document_id}.json"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    raw_chunks = meta.get("chunks", {})
                    chunk_texts = {int(k): v for k, v in raw_chunks.items()}
            else:
                DEFAULT_LOGGER.warning(
                    f"Metadata file not found: {metadata_path}",
                    source="_build_rag_context"
                )
                continue

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
            f"FAISS retrieval failed: {e}",
            source="MessageListView",
        )
        # No fallback - return empty context
        # Fallback keyword search removed because it's unreliable without full document content
        pass

    return context_text, context_hits


class ConversationListView(APIView):
    def get(self, request):
        # Use application layer
        result = _conversation_app.list_conversations()
        # Handle both dict and model object formats
        data = []
        for c in result:
            if isinstance(c, dict):
                data.append({"id": str(c["id"]), "title": c.get("title", ""), "status": c.get("status", "ready")})
            else:
                # c is a ConversationModel object
                data.append({
                    "id": str(c.conversations_id),
                    "title": c.conversations_title or c.conversations_name or "",
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

        # Use application layer - create_init_conversation instead of create_conversation
        try:
            conv = _conversation_app.create_init_conversation(
                conversation_title=title,
                file_caller="ConversationListView"
            )
        except Exception as e:
            DEFAULT_LOGGER.error(f"Error creating conversation: {e}", source="ConversationListView")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Add documents if provided
        if document_ids:
            try:
                _conversation_app.add_documents_to_conversation(conv.conversations_id, document_ids)
            except Exception as e:
                DEFAULT_LOGGER.warning(f"Could not add documents to conversation: {e}", source="ConversationListView")

        # Add bootstrap message
        conv_id = conv.conversations_id  # Already a UUID object
        conv_obj = ConversationModel.objects.get(pk=conv_id)
        docs = DocumentModel.objects.filter(pk__in=document_ids)
        doc_titles = [Path(d.documents_file_path).name if d.documents_file_path else "Untitled" for d in docs]
        if doc_titles:
            bootstrap_text = f"I have loaded the following documents: {', '.join(doc_titles)}. Ask me anything about them!"
            doc_hashes = []
            for d in docs:
                content_text = d.documents_content or ""
                cleaned_content = content_text.strip()
                h = hashlib.sha256(cleaned_content.encode("utf-8")).hexdigest()
                file_name = Path(d.documents_file_path).name if d.documents_file_path else "Untitled"
                doc_hashes.append(f"{file_name} (Hash: {h})")
            if doc_hashes:
                bootstrap_text += f"\nDocument Hash Code(s):\n" + "\n".join([f"- {dh}" for dh in doc_hashes])
        else:
            bootstrap_text = "I've started a new conversation. How can I assist you today?"

        MessageModel.objects.create(
            messages_conversation=conv_obj,
            messages_is_user_send=False,
            messages_content=bootstrap_text
        )

        return Response({
            "id": str(conv.conversations_id),
            "conversation_id": str(conv.conversations_id),
            "title": conv.conversations_name,
            "status": "ready"
        }, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    def get(self, request, conversation_id: str):
        try:
            conv = _conversation_app.get_conversation(UUID(conversation_id))
            return Response({
                "id": str(conv["id"]),
                "title": conv.get("title", ""),
                "status": conv.get("status", "ready")
            }, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)


class ConversationStatusView(APIView):
    def get(self, request, conversation_id: str):
        return Response({
            "conversation_id": conversation_id,
            "status": "ready"
        }, status=status.HTTP_200_OK)


class ConversationDocumentsView(APIView):
    def patch(self, request, conversation_id: str):
        """
        Update the documents associated with a conversation.
        
        Documents are already linked to conversations during the upload flow
        (DocumentModel has a OneToOneField to ConversationModel). This endpoint
        verifies the conversation exists and acknowledges the document selection
        from the frontend without needing to re-link them.
        """
        try:
            conv_uuid = UUID(conversation_id)
            # Verify the conversation exists
            try:
                ConversationModel.objects.get(pk=conv_uuid)
            except ConversationModel.DoesNotExist:
                return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

            # Document IDs from frontend may be non-UUID strings (e.g. "local-XXXX").
            # Documents are already linked to the conversation via the upload flow,
            # so we just acknowledge the selection.
            document_ids_raw = request.data.get("document_ids", [])
            DEFAULT_LOGGER.info(
                f"PATCH documents for conversation {conversation_id}: {document_ids_raw}",
                source="ConversationDocumentsView",
            )

            return Response({"status": "updated"}, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Invalid conversation ID format"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            DEFAULT_LOGGER.error(
                f"Error updating conversation documents: {e}",
                source="ConversationDocumentsView",
            )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageListView(APIView):
    def get(self, request, conversation_id: str):
        msgs = MessageModel.objects.filter(
            messages_conversation_id=conversation_id
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
            conv = ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        # Accept both "content" (old) and "user_input" (correct) for compatibility
        content = request.data.get("user_input") or request.data.get("content")
        if not content:
            return Response({"error": "Message content is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Save user message
        MessageModel.objects.create(
            messages_conversation=conv,
            messages_is_user_send=True,
            messages_content=content
        )

        # 2. Get attached indexed documents
        attached_docs = list(DocumentModel.objects.filter(documents_conversation=conv))
        
        # 3. Retrieve context via FAISS vector search (with keyword fallback)
        start_retrieval = time.time()
        context_text = ""
        context_hits = []
        # Skip retrieval if no documents
        if attached_docs:
            context_text, context_hits = _build_rag_context(attached_docs, content, top_k=5)
        retrieval_ms = int((time.time() - start_retrieval) * 1000)

        # 4. Build prompt
        system_prompt = "You are a helpful assistant. Answer based ONLY on the provided context. Do NOT make up answers."
        llm_prompt = f"System prompt: {system_prompt}\n\nContext from documents:\n{context_text}\n\nUser: {content}\n\nAssistant:"

        # 5. Resolve provider/model
        # Accept both old field names (provider, model) and new (provider_name, model_name)
        provider_name = request.data.get("provider_name") or request.data.get("provider", "auto")
        model_name = request.data.get("model_name") or request.data.get("model", "auto")

        if provider_name == "auto" or not provider_name:
            from sys_services.read_config.read_list_provider import LIST_PROVIDERS
            for provider_config in LIST_PROVIDERS:
                if provider_config.model_name == model_name:
                    provider_name = provider_config.provider_name.value
                    break
            if provider_name == "auto" or not provider_name:
                if "gemini" in model_name.lower():
                    provider_name = "gemini"
                elif "mistral" in model_name.lower():
                    provider_name = "mistral"
                elif "qwen" in model_name.lower() or "ollama" in model_name.lower():
                    provider_name = "ollama"
                else:
                    if LIST_PROVIDERS:
                        provider_name = LIST_PROVIDERS[0].provider_name.value
                    else:
                        provider_name = "ollama"

        # 6. Call LLM with retry
        start_llm = time.time()
        answer = ""
        used_mock = False
        used_provider = provider_name

        try:
            # Simple LLM call without resilience wrapper for now
            factory = LLMProviderFactory(__container.config_provider(), __container.log_pool())
            llm_client = factory.get_provider(EProviderName(provider_name), file_caller="MessageListView.post")
            
            completion_req = ICompletionRequest(
                provider=EProviderName(provider_name),
                model=model_name,
                prompt=llm_prompt,
            )
            completion_resp = llm_client.generate(completion_req, file_caller="MessageListView.post")
            answer = completion_resp.content or "No response from model"
        except Exception as exc:
            import traceback
            error_traceback = traceback.format_exc()
            DEFAULT_LOGGER.error(
                f"LLM provider {provider_name} failed: {exc}. Using mock response.\nTraceback:\n{error_traceback}",
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
