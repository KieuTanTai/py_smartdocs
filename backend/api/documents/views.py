from __future__ import annotations

from email import message
import hashlib
import json
from logging import config
import os
import tempfile
import time
from pathlib import Path
import traceback

from ollama import embed

from backend.apps.config import container
from backend.apps.core.interfaces.dataclass.application.i_message_response import ISendMessageResponse
from backend.apps.core.interfaces.dataclass.request.i_create_conversation_request import ICreateConversationRequest, IGetConversationRequest, IGetMessageByConversationRequest, ISendMessageRequest
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
import numpy as np
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from backend.apps.services.chat.models import DocumentModel
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.core.chunk.chunker import Chunker
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.services.rag_base.locate.locate_service import LocateService

from backend.apps.application.conversations.application import ConversationApplication
from backend.apps.utils.get_instance_model_database import get_embedding_model, get_model_name
from sys_services.read_config import config_provider
from sys_services.system_dirs import METADATA_DIR

# Singleton application instances
_container = container.BackendContainer()

class DocumentListView(APIView):
    def get(self, request):
        doc_app = _container.document_application()
        
        result = doc_app.list_files(str(request.data.get("conversation_id")), file_caller="DocumentListView")
        cloud_ids = result.cloud_ids
        names = result.names
        
        data = dict(zip(cloud_ids,names))
        
        return Response(data, status=status.HTTP_200_OK)

class DocumentUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        sys_logger = _container.log_pool() 

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            sys_logger.error(f"No file in request.FILES. FILES keys: {list(request.FILES.keys())}, POST keys: {list(request.POST.keys())}", source="DocumentUploadView", call_by="post")
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sys_logger.info(f"Received file upload: {uploaded_file.name}, size: {uploaded_file.size}", source="DocumentUploadView", call_by="post")

        # Save uploaded file to a temporary file on disk using its original name
        temp_dir = Path(tempfile.gettempdir()) / "smartdocs_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = temp_dir / uploaded_file.name

        try:
            with open(temp_file_path, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Validate and convert provider
            provider_str = request.POST.get("provider") or request.data.get("provider", "gemini")
            provider_str = provider_str.lower()
            valid_providers = {"gemini", "mistral", "ollama"}
            
            # Convert "auto" to default provider
            if provider_str == "auto" or provider_str not in valid_providers:
                provider_str = "gemini"  # Default provider
            
            try:
                provider_name = EProviderName(provider_str)
            except ValueError:
                return Response(
                    {"error": f"Invalid provider: {provider_str}. Valid options: {', '.join(valid_providers)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            config_provider = _container.config_provider()
            embeding_model_name = get_embedding_model(config_provider, provider_name)
            model_name = get_model_name(config_provider, provider_name)
            
            sys_logger.info(f"Using provider: {provider_name.value}, model: {model_name}, embedding: {embeding_model_name}", source="DocumentUploadView", call_by="post")

            document_urls = request.POST.get("document_urls") or request.data.get("document_urls")
            if not document_urls:
                document_urls = []
            elif isinstance(document_urls, str):
                try:
                    document_urls = json.loads(document_urls)
                except Exception:
                    document_urls = [document_urls]

            pipeline_type_str = request.POST.get("type") or request.data.get("type") or "base"
            try:
                pipeline_type = EPipelineType(pipeline_type_str)
            except ValueError:
                pipeline_type = EPipelineType.BASE

            create_req = ICreateConversationRequest(
                provider=provider_name,
                model_name=model_name,
                document_urls=document_urls,
                document_paths=[temp_file_path],
                type=pipeline_type,
                conversation_id=request.POST.get("conversation_id") or request.data.get("conversation_id"),
                embedding_model_name=embeding_model_name,
            )

            conversation = _container.conversation_application()
            cons = conversation.create_init_conversation()
            create_req.conversation_id = cons.conversations_id
            doc_app = _container.document_application()
            
            response = doc_app.upload_document(create_req, Path(__file__).name)
            conversation.run_application_pipeline(create_req.provider, create_req.model_name, cons, response.info.summarize, Path(__file__).name)
            conversation.rename_conversation(str(cons.conversations_id), response.info.conversation_title, Path(__file__).name)
            
            sys_logger.info(f"File uploaded successfully: {conversation.list_conversations}", source="DocumentUploadView", call_by="post")
            
            # Get the created document ID to return to the caller
            doc_id = None
            try:
                doc_obj = DocumentModel.objects.filter(documents_conversation=cons).first()
                if doc_obj:
                    doc_id = str(doc_obj.document_id)
            except Exception as e:
                sys_logger.error(f"Error getting document ID: {e}", source="DocumentUploadView", call_by="post")

            # Convert response to JSON-serializable format
            response_data = {
                "id": doc_id,
                "document_id": doc_id,
                "conversation_id": str(cons.conversations_id),
                "conversation_name": response.info.conversation_name,
                "conversation_title": response.info.conversation_title,
                "provider": response.info.provider.value,
                "model_name": response.info.model_name,
                "summarize": response.info.summarize,
                "document_urls": response.info.document_urls,
                "document_paths": [str(path) for path in response.info.document_paths],
                "type": response.info.type.value,
            }
            
            if response.time_counter:
                response_data["time_counter"] = {
                    "extract_time": response.time_counter.extract_time,
                    "chunk_time": response.time_counter.chunk_time,
                    "embedding_time": response.time_counter.embedding_time,
                    "save_time": response.time_counter.save_time,
                    "total_time": response.time_counter.total_time,
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            sys_logger.error(f"Validation Error: {e}", source="DocumentUploadView", call_by="post", method_call="upload_document")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            sys_logger.error(f"Upload failed: {e}\n{traceback.format_exc()}", source="DocumentUploadView", call_by="post")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            try:
                if temp_file_path.exists():
                    temp_file_path.unlink()
            except Exception:
                pass
            sys_logger.flush()

class ConversationListView(APIView):
    def get(self, request):
        sys_logger = _container.log_pool() 
        try:
            conversation = _container.conversation_application()
            response = conversation.list_conversations()
            return Response({
                "response": response,
                "status": "u"
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            sys_logger.error(f"Validation Error: {e}", source="ConversationListView", call_by="get", method_call="list_conversation")

class MessageListViewByConversation(APIView):
    def get(self, request):
        sys_logger = _container.log_pool()
        try:
            message_app = _container.message_application()
            
            return message_app.get_conversation_messages(str(request.data.get("convesation_id")),50,0,Path(__file__).name)
        except ValueError as e:
            sys_logger.error(f"Validation Error: {e}", source="MessageListViewByConversation", call_by="get", method_call="get_conversation_messages")
            
    def post(self, request):
        sys_logger = _container.log_pool()
        try:
            message_app = _container.message_application()
            
            send_msg_req = ISendMessageRequest(
                request.data.get("user_input"),
                request.data.get("provider_name"),
                request.data.get("model_name"),
                request.data.get("pipeline_type"),
                request.data.get("conversation_id")
            )
            return message_app.send_message(str(request.conversation_id), request.user_input, request.provider_name, request.model_name, request.pipeline_type, Path(__file__).name)
            
        except ValueError as e:
            sys_logger.error(f"Validation Error: {e}", source="MessageListViewByConversation", call_by="post", method_call="send_message")
            
