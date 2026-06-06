from __future__ import annotations

import os
import uuid
import time
import logging
from pathlib import Path
import pypdf

from django.urls import path
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from backend.apps.services.chat.models import ConversationModel, MessageModel, DocumentModel, ConversationFilesModel
from backend.apps.services.chat.serializers import ConversationSerializer, MessageSerializer, DocumentSerializer
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.core.chunk.chunker import Chunker
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName

# Initialize logger
logger = logging.getLogger(__name__)


# Health Check View
class HealthView(APIView):
    def get(self, request):
        return Response({
            "status": "healthy",
            "message": "SmartDocs API is running"
        }, status=status.HTTP_200_OK)


# Provider Management Views
class ProviderListView(APIView):
    def get(self, request):
        """Get list of configured providers"""
        try:
            factory = LLMProviderFactory(DEFAULT_CONFIG_PROVIDER, logger)
            providers = factory.get_available_providers()
            return Response({
                "providers": providers,
                "count": len(providers)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to get providers: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProviderTestView(APIView):
    def post(self, request):
        """Test a specific provider connection"""
        provider_name = request.data.get("provider")
        model_name = request.data.get("model")
        
        if not provider_name or not model_name:
            return Response({
                "error": "provider and model parameters are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            factory = LLMProviderFactory(DEFAULT_CONFIG_PROVIDER, logger)
            client = factory.get_provider(provider_name)
            req = ICompletionRequest(
                provider=EProviderName(provider_name),
                model=model_name,
                prompt="Test message",
                context_hits=[]
            )
            response = client.generate(req)
            return Response({
                "status": "success",
                "provider": provider_name,
                "model": model_name,
                "response": response[:100] + "..." if len(response) > 100 else response
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            return Response({
                "status": "failed",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Document Management Views
class DocumentListView(APIView):
    def get(self, request):
        docs = DocumentModel.objects.all().order_by("-faiss_index_created_at")
        data = []
        for d in docs:
            data.append({
                "id": str(d.faiss_index_id),
                "title": d.faiss_index_file_name,
                "status": d.status,
                "source": "local"
            })
        return Response(data, status=status.HTTP_200_OK)


class DocumentUploadView(APIView):
    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file to media directory
        media_dir = Path(settings.MEDIA_ROOT)
        media_dir.mkdir(parents=True, exist_ok=True)
        file_path = media_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
                
        # Create DocumentModel record
        doc = DocumentModel.objects.create(
            faiss_index_file_name=uploaded_file.name,
            file_path=str(file_path),
            status="uploaded"
        )
        
        return Response({
            "id": str(doc.faiss_index_id),
            "title": doc.faiss_index_file_name,
            "status": "uploaded"
        }, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    def get(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            return Response({
                "id": str(doc.faiss_index_id),
                "title": doc.faiss_index_file_name,
                "status": doc.status
            }, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except Exception:
                    pass
            doc.delete()
            return Response({"status": "deleted"}, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)


class DocumentStatusView(APIView):
    def get(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            return Response({
                "id": str(doc.faiss_index_id),
                "status": doc.status
            }, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)


class DocumentIndexView(APIView):
    def post(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            doc.status = "processing"
            doc.save()
            
            # Read file and extract text
            extracted_text = ""
            if doc.file_path and os.path.exists(doc.file_path):
                if doc.file_path.endswith(".pdf"):
                    try:
                        reader = pypdf.PdfReader(doc.file_path)
                        text_list = []
                        for page in reader.pages:
                            t = page.extract_text()
                            if t:
                                text_list.append(t)
                        extracted_text = "\n".join(text_list)
                    except Exception as e:
                        logger.error(f"Failed to read PDF: {e}")
                else:
                    try:
                        with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
                            extracted_text = f.read()
                    except Exception as e:
                        logger.error(f"Failed to read text file: {e}")
            
            # Normalize text
            normalizer = Normalize()
            normalized_text = normalizer.normalize(extracted_text)
            
            doc.content = normalized_text
            doc.status = "indexed"
            doc.save()
            
            return Response({
                "id": str(doc.faiss_index_id),
                "status": "indexed"
            }, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)


class DocumentBulkIndexView(APIView):
    def post(self, request):
        return Response({"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED)


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
        
        # 5. Invoke LLM client
        model_name = request.data.get("model", "gemini-2.5-flash")
        provider_name = request.data.get("provider", "gemini")

        start_time = time.time()
        answer = ""
        used_mock = False
        
        try:
            factory = LLMProviderFactory(DEFAULT_CONFIG_PROVIDER, logger)
            client = factory.get_provider(provider_name)
            req = ICompletionRequest(
                provider=EProviderName(provider_name),
                model=model_name,
                prompt=llm_prompt,
                context_hits=context_hits
            )
            answer = client.generate(req)
        except Exception as exc:
            logger.error(f"LLM execution error: {exc}. Using mock response.")
            answer = f"I failed to connect to {provider_name} ({model_name}). Here is a simulated response based on the context: {context_text[:200]}"
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


class CoreSearchView(APIView):
    def post(self, request):
        return Response({"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED)

urlpatterns = [
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/providers/", ProviderListView.as_view(), name="providers"),
    path("api/providers/test/", ProviderTestView.as_view(), name="providers-test"),
    path("api/documents/", DocumentListView.as_view(), name="documents-list"),
    path("api/documents/upload/", DocumentUploadView.as_view(), name="documents-upload"),
    path("api/documents/<str:document_id>/", DocumentDetailView.as_view(), name="documents-detail"),
    path("api/documents/<str:document_id>/status/", DocumentStatusView.as_view(), name="documents-status"),
    path("api/documents/<str:document_id>/index/", DocumentIndexView.as_view(), name="documents-index"),
    path("api/documents/index/bulk/", DocumentBulkIndexView.as_view(), name="documents-index-bulk"),
    
    path("api/conversations/", ConversationListView.as_view(), name="conversations"),
    path("api/conversations/<str:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("api/conversations/<str:conversation_id>/status/", ConversationStatusView.as_view(), name="conversation-status"),
    path("api/conversations/<str:conversation_id>/documents/", ConversationDocumentsView.as_view(), name="conversation-documents"),
    path("api/conversations/<str:conversation_id>/messages/", MessageListView.as_view(), name="messages"),
    
    path("api/application/conversations/", ConversationListView.as_view(), name="app-conversations"),
    path("api/application/conversations/<str:conversation_id>/", ConversationDetailView.as_view(), name="app-conversation-detail"),
    path("api/application/conversations/<str:conversation_id>/status/", ConversationStatusView.as_view(), name="app-conversation-status"),
    path("api/application/conversations/<str:conversation_id>/documents/", ConversationDocumentsView.as_view(), name="app-conversation-documents"),
    path("api/application/conversations/<str:conversation_id>/messages/", MessageListView.as_view(), name="app-messages"),
    
    path("api/core/search/", CoreSearchView.as_view(), name="core-search"),
    
]
