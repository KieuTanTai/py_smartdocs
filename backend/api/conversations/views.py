from __future__ import annotations

import datetime
import hashlib
import json
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import cast
from uuid import UUID

import numpy as np
from django.conf import settings
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
__container = container.BackendContainer()


def _jsonable(value):
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


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
        factory = LLMProviderFactory(__container.config_provider(), __container.log_pool())
        embed_client = factory.get_provider(embed_provider)

        embed_req = ICompletionRequest(
            provider=embed_provider,
            model=embed_model,
            prompt=user_query,
        )
        query_vector_resp = embed_client.embedding(embed_req)
        query_vector = query_vector_resp.embedding.reshape(1, -1).astype(np.float32)

        locate_service = LocateService(metadata_dir=METADATA_DIR, logger=__container.log_pool())
        faiss_service = cast(
            IVectorStoreService,
            locate_service.get_vector_store(EBackendStorageName.FAISS),
        )

        all_results: list[tuple[float, str]] = []

        for doc in indexed_docs:
            # Load FAISS index for this document
            try:
                load_resp = faiss_service.load(doc.documents_conversation.conversations_id)
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
        doc_contents = [d.content for d in indexed_docs if d.content]
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
        data = [
            {"id": str(c["id"]), "title": c.get("title", ""), "status": c.get("status", "ready")}
            for c in result
        ]
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

        # Use application layer
        try:
            conv = _conversation_app.create_conversation(
                title=title,
                provider_name=provider,
                model_name=model,
                system_prompt=system_prompt,
                document_ids=document_ids if document_ids else None,
            )
        except Exception as e:
            DEFAULT_LOGGER.error(f"Error creating conversation: {e}", source="ConversationListView")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Add bootstrap message (application layer doesn't do this)
        conv_id = UUID(conv["id"])
        conv_obj = ConversationModel.objects.get(pk=conv_id)
        docs = DocumentModel.objects.filter(pk__in=document_ids)
        doc_titles = [d.faiss_index_file_name for d in docs]
        if doc_titles:
            bootstrap_text = f"I have loaded the following documents: {', '.join(doc_titles)}. Ask me anything about them!"
            doc_hashes = []
            for d in docs:
                content_text = d.content or ""
                cleaned_content = content_text.strip()
                h = hashlib.sha256(cleaned_content.encode("utf-8")).hexdigest()
                doc_hashes.append(f"{d.faiss_index_file_name} (Hash: {h})")
            if doc_hashes:
                bootstrap_text += f"\nDocument Hash Code(s):\n" + "\n".join([f"- {dh}" for dh in doc_hashes])
        else:
            bootstrap_text = "I've started a new conversation. How can I assist you today?"

        MessageModel.objects.create(
            message_conversation=conv_obj,
            message_is_user_send=False,
            message_content=bootstrap_text
        )

        return Response({
            "conversation_id": conv["id"],
            "title": conv.get("title", ""),
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
        try:
            conv_uuid = UUID(conversation_id)
            document_ids_raw = request.data.get("document_ids", [])
            document_ids = []
            for doc_id in document_ids_raw:
                try:
                    document_ids.append(UUID(str(doc_id)))
                except (ValueError, TypeError):
                    pass

            _conversation_app.add_documents_to_conversation(conv_uuid, document_ids)
            return Response({"status": "updated"}, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageListView(APIView):
    def get(self, request, conversation_id: str):
        try:
            message_app = __container.message_application()
            result = message_app.get_conversation_messages(
                conversation_id,
                limit=int(request.query_params.get("limit", 50)),
                offset=int(request.query_params.get("offset", 0)),
                file_caller=Path(__file__).name,
            )
            return Response(_jsonable(result), status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, conversation_id: str):
        content = request.data.get("user_input") or request.data.get("content")
        provider_name = request.data.get("provider_name") or request.data.get("provider")
        model_name = request.data.get("model_name") or request.data.get("model")
        pipeline_type = request.data.get("pipeline_type") or request.data.get("mode") or "base"
        if pipeline_type == "normal":
            pipeline_type = "base"
        if provider_name == "auto" or not provider_name:
            from sys_services.read_config.read_list_provider import LIST_PROVIDERS

            provider_name = ""
            for provider_config in LIST_PROVIDERS:
                if provider_config.model_name == model_name:
                    provider_name = provider_config.provider_name.value
                    break
            if not provider_name:
                if model_name and "gemini" in model_name.lower():
                    provider_name = "gemini"
                elif model_name and "mistral" in model_name.lower():
                    provider_name = "mistral"
                elif model_name and ("qwen" in model_name.lower() or "ollama" in model_name.lower()):
                    provider_name = "ollama"
                elif LIST_PROVIDERS:
                    provider_name = LIST_PROVIDERS[0].provider_name.value
                else:
                    provider_name = "ollama"

        try:
            message_app = __container.message_application()
            result = message_app.send_message(
                conversation_id=conversation_id,
                user_input=content,
                provider_name=provider_name,
                model_name=model_name,
                pipeline_type=pipeline_type,
                file_caller=Path(__file__).name,
            )
            data = _jsonable(result)
            data["assistant"] = data.get("assistant_message", "")
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
