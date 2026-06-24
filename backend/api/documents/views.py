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
import uuid

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

from backend.apps.services.chat.models import DocumentModel
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
        paths = [Path(file) for file in uploaded_file]
        provider_name = EProviderName(request.data.get("provider"))
        config_provider = _container.config_provider()
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
            response_json={
                "conversation_id": create_req.conversation_id,
                "title": response.info.conversation_title,
                "provider": response.info.provider.value,
                "model_name": response.info.model_name,
                "type": response.info.type.value,
                "create_at": response.info.create_at
            }
            
            return Response(response_json, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            sys_logger.error(f"Validation Error: {e}", source="DocumentUploadView", call_by="post", method_call="upload_document")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            sys_logger.error(f"Upload failed: {e}\n{traceback.format_exc()}", source="DocumentUploadView", call_by="post")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
    sys_logger = _container.log_pool()
    def get(self, request):
        try:
            message_app = _container.message_application()

            return message_app.get_conversation_messages(str(request.query_params.get("conversation_id")),50,0,Path(__file__).name)
        except ValueError as e:
            self.sys_logger.error(f"Validation Error: {e}", source="MessageListViewByConversation", call_by="get", method_call="get_conversation_messages")

class SendMesssage(APIView):
    sys_logger = _container.log_pool()
    def post(self, request):
        self.sys_logger.info(f"Received message request: {request.data}", source="MessageListViewByConversation", call_by="post", method_call="send_message")
        try:

            message_app = _container.message_application()
            config_provider = _container.config_provider()
            user_input=request.data.get("content")
            print(f"User input: {user_input}")
            provider_name = EProviderName(request.data.get("provider"))
            print(f"Provider: {provider_name}")
            model_name = get_model_name(config_provider,provider_name)
            print(f"model_name: {model_name}")
            pipeline_type = EPipelineType.BASE
            conversation_id= request.data.get("conversation_id")
            embedding_model_name= get_embedding_model(config_provider,provider_name)
            print(f"embedding_model_name: {embedding_model_name}")
            print(f"conversation_id: {conversation_id}")
            send_msg_req = ISendMessageRequest(
                user_input=user_input,
                provider_name=provider_name,
                model_name=model_name,
                pipeline_type=pipeline_type,
                conversation_id=conversation_id,
            )
            response_data=message_app.send_message(str(conversation_id), user_input, provider_name, model_name, embedding_model_name,pipeline_type, Path(__file__).name)
            print(f"response_data.user_message_id: {response_data.user_message_id}")
            print(f"response_data.assistant_message_id: {response_data.assistant_message_id}")
            response_json ={
                "user_message_id": response_data.user_message_id,
                "assistant_message_id": response_data.assistant_message_id,
                "assistant_message": response_data.assistant_message,
                "latency_ms": response_data.latency_ms
            }
            return Response(response_json, status=status.HTTP_201_CREATED)

        except ValueError as e:
            self.sys_logger.error(f"Validation Error: {e}", source="MessageListViewByConversation", call_by="post", method_call="send_message")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(traceback.format_exc())
            self.sys_logger.error(
                f"Unexpected Error: {e}\n{traceback.format_exc()}",
                source="MessageListViewByConversation",
                call_by="post",
                method_call="send_message"
            )
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            self.sys_logger.flush()
