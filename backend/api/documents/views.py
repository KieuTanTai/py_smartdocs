from __future__ import annotations

from dataclasses import asdict
from email import message
import hashlib
import json
from logging import config
import os
import time
from pathlib import Path
import traceback

from ollama import embed

from backend.apps.config import container
from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.interfaces.dataclass.application.i_message_response import ISendMessageResponse
from backend.apps.core.interfaces.dataclass.request.i_create_conversation_request import ICreateConversationRequest, IGetConversationRequest, IGetMessageByConversationRequest, ISendMessageRequest
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
import numpy as np
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from backend.apps.services.chat.models import ConversationFilesModel, DocumentModel
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.core.chunk.chunker import Chunker
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.services.rag_base.locate.locate_service import LocateService

from backend.apps.application.conversations.application import ConversationApplication
from backend.apps.utils.get_instance_model_database import get_embedding_model, get_model_name
from sys_services.read_config import config_provider
from sys_services.system_dirs import METADATA_DIR

# Singleton application instances
_container = container.BackendContainer()


def _resolve_upload_provider(provider_or_model: str | None) -> EProviderName:
    value = (provider_or_model or "").strip()
    config = _container.config_provider()

    for provider in EProviderName:
        if value == provider.value:
            return provider

    for configured in config.get_list_providers():
        if value in {
            configured.model_name,
            configured.embed_model_name,
            configured.provider_name.value,
        }:
            return configured.provider_name

    ollama = next(
        (
            configured
            for configured in config.get_list_providers()
            if configured.provider_name == EProviderName.OLLAMA
        ),
        None,
    )
    if ollama:
        return ollama.provider_name

    configured = config.get_list_providers()
    if configured:
        return configured[0].provider_name

    return EProviderName.OLLAMA

class DocumentListView(APIView):
    def get(self, request):
        doc_app = _container.document_application()
        
        result = doc_app.list_files(str(request.data.get("conversation_id")), file_caller="DocumentListView")
        cloud_ids = result.cloud_ids
        names = result.names
        
        data = dict(zip(cloud_ids,names))
        
        return Response(data, status=status.HTTP_200_OK)

class DocumentUploadView(APIView):
    def post(self, request):
        sys_logger = _container.log_pool() 
        uploaded_file = request.data.get("document_urls")
        if not uploaded_file:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        config_provider = _container.config_provider()
        paths = [Path(file) for file in uploaded_file]
        provider_name = _resolve_upload_provider(request.data.get("provider"))
        embeding_model_name = get_embedding_model(config_provider,provider_name)
        model_name = get_model_name(config_provider, provider_name)
        type = EPipelineType(request.data.get("type"))
        sys_logger.info(f"{provider_name}",
                         Path(__file__).name)
        sys_logger.flush()
        create_req = ICreateConversationRequest(
            provider=provider_name,
            model_name=model_name,
            document_urls=request.data.get("document_urls"),
            document_paths=paths,
            type=type,
            conversation_id=request.data.get("conversation_id"),
            embedding_model_name=embeding_model_name,
        )
        print(asdict(create_req))
        if not uploaded_file:
            sys_logger.warning("No file uploaded in request", source="DocumentUploadView", call_by="post")
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            conversation = _container.conversation_application()
            cons = conversation.create_init_conversation()
            print(cons.conversations_id)
            create_req.conversation_id = cons.conversations_id
            doc_app = _container.document_application()
            
            response = doc_app.upload_document(create_req, Path(__file__).name)
            conversation.run_application_pipeline(create_req.provider, create_req.model_name, cons, response.info.summarize, Path(__file__).name)
            conversation.rename_conversation(str(cons.conversations_id), response.info.conversation_title, Path(__file__).name)
            
            sys_logger.info(f"File uploaded successfully: {conversation.list_conversations}", source="DocumentUploadView", call_by="post")
            
            document_model = DocumentModel.objects.filter(documents_conversation=cons).first()
            file_ids = []
            if document_model:
                file_ids = [
                    str(item.conversation_files_cloud_id)
                    for item in ConversationFilesModel.objects.filter(
                        conversation_files_document=document_model
                    )
                ]

            # Convert response to JSON-serializable dict
            response_data = {
                "id": str(cons.conversations_id),
                "conversation_id": str(cons.conversations_id),
                "document_id": str(document_model.document_id) if document_model else "",
                "document_model_id": str(document_model.document_id) if document_model else "",
                "file_ids": file_ids,
                "title": response.info.conversation_title,
                "status": "indexed",
                "provider": response.info.provider.value,
                "model_name": response.info.model_name,
                "document_urls": response.info.document_urls,
                "type": response.info.type.value,
                "summarize": response.info.summarize,
            }
            
            # Add time counter if available
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
            error_msg = str(e)
            sys_logger.error(f"Validation Error: {error_msg}", source="DocumentUploadView", call_by="post", method_call="upload_document")
            sys_logger.flush()
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            sys_logger.error(f"Upload failed: {error_msg}\n{traceback_str}", source="DocumentUploadView", call_by="post")
            sys_logger.flush()
            return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
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
            
