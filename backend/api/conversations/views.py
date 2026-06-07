from __future__ import annotations

import datetime
import hashlib
import time

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from backend.apps.services.chat.models import (
    ConversationModel,
    MessageModel,
    DocumentModel,
    ConversationFilesModel,
)
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.logging import DEFAULT_LOGGER


class ConversationListView(APIView):
    def get(self, request):
        convs = ConversationModel.objects.all().order_by("-conversation_created_at")
        data = []
        for c in convs:
            data.append({
                "id": str(c.conversation_id),
                "title": c.conversation_title,
                "status": "ready"
            })
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        title = request.data.get("title", "New Conversation")
        provider = request.data.get("provider", "auto")
        model = request.data.get("model", "auto")
        system_prompt = request.data.get("system_prompt", "")
        document_ids = request.data.get("document_ids", [])

        # Append current datetime to the title
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"{title} - {now_str}"

        # Create conversation
        conv = ConversationModel.objects.create(
            conversation_title=title
        )

        # Save config context if needed or link documents
        docs = []
        for doc_id in document_ids:
            try:
                doc = DocumentModel.objects.get(pk=doc_id)
                ConversationFilesModel.objects.create(
                    conversation=conv,
                    faiss_index=doc
                )
                docs.append(doc)
            except DocumentModel.DoesNotExist:
                pass

        # Generate initial bootstrap summary message
        doc_titles = [d.faiss_index_file_name for d in docs]
        if doc_titles:
            bootstrap_text = f"I have loaded the following documents: {', '.join(doc_titles)}. Ask me anything about them!"
            # Calculate and append SHA256 hashes of document content
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
            message_conversation=conv,
            message_is_user_send=False,
            message_content=bootstrap_text
        )

        return Response({
            "conversation_id": str(conv.conversation_id),
            "title": conv.conversation_title,
            "status": "ready"
        }, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    def get(self, request, conversation_id: str):
        try:
            conv = ConversationModel.objects.get(pk=conversation_id)
            return Response({
                "id": str(conv.conversation_id),
                "title": conv.conversation_title,
                "status": "ready"
            }, status=status.HTTP_200_OK)
        except ConversationModel.DoesNotExist:
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
            conv = ConversationModel.objects.get(pk=conversation_id)
            document_ids = request.data.get("document_ids", [])

            # Clear old and set new
            ConversationFilesModel.objects.filter(conversation=conv).delete()
            for doc_id in document_ids:
                try:
                    doc = DocumentModel.objects.get(pk=doc_id)
                    ConversationFilesModel.objects.create(
                        conversation=conv,
                        faiss_index=doc
                    )
                except DocumentModel.DoesNotExist:
                    pass
            return Response({"status": "updated"}, status=status.HTTP_200_OK)
        except ConversationModel.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)


class MessageListView(APIView):
    def get(self, request, conversation_id: str):
        msgs = MessageModel.objects.filter(message_conversation_id=conversation_id).order_by("message_created_at")
        data = []
        for m in msgs:
            data.append({
                "role": "user" if m.message_is_user_send else "assistant",
                "content": m.message_content
            })
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, conversation_id: str):
        try:
            conv = ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        content = request.data.get("content")
        if not content:
            return Response({"error": "Message content is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Save user message
        MessageModel.objects.create(
            message_conversation=conv,
            message_is_user_send=True,
            message_content=content
        )

        # 2. Get attached documents
        file_mappings = ConversationFilesModel.objects.filter(conversation=conv)
        doc_contents = []
        for mapping in file_mappings:
            if mapping.faiss_index.content:
                doc_contents.append(mapping.faiss_index.content)

        # 3. Retrieve context hits using keyword paragraph search (Offline RAG)
        context_text = ""
        context_hits = []
        if doc_contents:
            paragraphs = []
            for doc_text in doc_contents:
                paragraphs.extend([p.strip() for p in doc_text.split("\n") if p.strip()])

            query_words = set(content.lower().split())
            scored_paragraphs = []
            for p in paragraphs:
                p_words = set(p.lower().split())
                score = len(query_words.intersection(p_words))
                if score > 0:
                    scored_paragraphs.append((score, p))

            scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
            top_paragraphs = [p for score, p in scored_paragraphs[:5]]
            context_text = "\n".join(top_paragraphs)
            for score, p in scored_paragraphs[:5]:
                context_hits.append({"text": p[:200] + "...", "score": score})

        # 4. Build Prompt Context
        system_prompt = "You are a helpful assistant."
        llm_prompt = f"System prompt: {system_prompt}\n\nContext from documents:\n{context_text}\n\nUser: {content}\n\nAssistant:"

        provider_name = request.data.get("provider", "ollama")
        model_name = request.data.get("model", "qwen2.5:1.5b-instruct")

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

        start_time = time.time()
        answer = ""
        used_mock = False

        try:
            factory = LLMProviderFactory(DEFAULT_CONFIG_PROVIDER, DEFAULT_LOGGER)
            client = factory.get_provider(provider_name)
            req = ICompletionRequest(
                provider=EProviderName(provider_name),
                model=model_name,
                prompt=llm_prompt,
                context_hits=context_hits
            )
            answer = client.generate(req)
        except Exception as exc:
            DEFAULT_LOGGER.error(f"LLM execution error: {exc}. Using mock response.")
            if context_text:
                answer = (
                    f"⚠️ **Không thể kết nối đến model {provider_name} ({model_name}).**\n\n"
                    f"Dưới đây là nội dung tài liệu trích xuất từ ngữ cảnh (Simulated Response):\n\n"
                    f"{context_text}"
                )
            else:
                answer = (
                    f"⚠️ **Không thể kết nối đến model {provider_name} ({model_name}).**\n\n"
                    f"Không tìm thấy ngữ cảnh phù hợp trong tài liệu để trả lời."
                )
            used_mock = True

        latency_ms = int((time.time() - start_time) * 1000)

        # 6. Save assistant message
        MessageModel.objects.create(
            message_conversation=conv,
            message_is_user_send=False,
            message_content=answer
        )

        return Response({
            "conversation_id": str(conv.conversation_id),
            "assistant": answer,
            "used_mock": used_mock,
            "metrics": {
                "provider": provider_name,
                "model": model_name,
                "total_ms": latency_ms,
                "embed_ms": 0,
                "query_ms": 0,
                "response_ms": latency_ms,
                "retrieval_hits": context_hits
            }
        }, status=status.HTTP_200_OK)
