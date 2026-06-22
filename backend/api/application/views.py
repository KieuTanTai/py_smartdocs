"""
Application API Views.
Chỉ validate lớp 1 (request format) rồi gọi application/ layer.
Luồng: api/ → application/ → job/ → tasks/ → core/, llm/, services/
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.request.i_run_application_request import (
    IDeleteConversationApplicationRequest,
    ISendMessageApplicationRequest,
    IUploadApplicationRequest,
)
from backend.apps.interfaces.application.i_run_application import IRunApplication

# Resolve application instance từ DI container
_container = BackendContainer()
_run_application: IRunApplication = _container.run_application()


class ApplicationUploadView(APIView):
    """POST /api/application/upload/
    Upload files, tạo conversation, chạy pipeline xử lý.
    Field contract response: id, title, status, conversation_id, date_create.
    """

    def post(self, request):
        # Validate lớp 1: kiểm tra request format
        files = request.FILES.getlist("files")
        provider_name = request.data.get("provider")
        model_name = request.data.get("model_name")
        pipeline_type = request.data.get("type", "normal")

        if not provider_name:
            return Response(
                {"error": "provider is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not model_name:
            return Response(
                {"error": "model_name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not files:
            return Response(
                {"error": "At least one file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate provider enum
        try:
            provider = EProviderName(provider_name.lower())
        except ValueError:
            return Response(
                {"error": f"Invalid provider '{provider_name}'. Must be one of: {[e.value for e in EProviderName]}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lưu file tạm vào disk để lấy path
        saved_paths: List[Path] = []
        try:
            from django.conf import settings

            upload_dir = Path(settings.MEDIA_ROOT) / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)

            for uploaded_file in files:
                file_path = upload_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                saved_paths.append(file_path)
        except Exception as exc:
            return Response(
                {"error": f"Failed to save uploaded files: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Gọi application layer
        try:
            app_request = IUploadApplicationRequest(
                provider=provider,
                model_name=model_name,
                document_paths=saved_paths,
                type=pipeline_type,
            )
            response = _run_application.upload(app_request)

            return Response(
                {
                    "id": response.id,
                    "title": response.title,
                    "status": response.status,
                    "conversation_id": response.conversation_id,
                    "date_create": response.date_create,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApplicationConversationListView(APIView):
    """GET /api/application/conversations/
    List all conversations.
    Field contract response: conversation_id, status, date_create.
    """

    def get(self, request):
        try:
            conversations = _run_application.list_conversations()
            data = [
                {
                    "conversation_id": c.conversation_id,
                    "status": c.status,
                    "date_create": c.date_create,
                    "title": c.title,
                }
                for c in conversations
            ]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApplicationConversationView(APIView):
    """GET/DELETE /api/application/conversations/<id>/
    Get or delete a single conversation.
    Field contract response (GET): conversation_id, status, date_create.
    """

    def get(self, request, conversation_id: str):
        try:
            response = _run_application.get_conversation(conversation_id)
            return Response(
                {
                    "conversation_id": response.conversation_id,
                    "status": response.status,
                    "date_create": response.date_create,
                    "title": response.title,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request, conversation_id: str):
        try:
            delete_request = IDeleteConversationApplicationRequest(
                conversation_id=conversation_id,
            )
            _run_application.delete_conversation(delete_request)
            return Response(
                {"status": "deleted", "conversation_id": conversation_id},
                status=status.HTTP_200_OK,
            )
        except ValueError:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ApplicationMessageView(APIView):
    """POST /api/application/conversations/<id>/messages/
    Gửi message vào conversation, RAG retrieval + LLM generate.
    Field contract response: message, used_mock, conversation_id.
    """

    def post(self, request, conversation_id: str):
        # Validate lớp 1
        content = request.data.get("content") or request.data.get("message")
        provider_name = request.data.get("provider")
        model_name = request.data.get("model_name")
        pipeline_type = request.data.get("type", "normal")

        if not content:
            return Response(
                {"error": "content (or message) is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not provider_name:
            return Response(
                {"error": "provider is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not model_name:
            return Response(
                {"error": "model_name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate provider enum
        try:
            provider = EProviderName(provider_name.lower())
        except ValueError:
            return Response(
                {"error": f"Invalid provider '{provider_name}'. Must be one of: {[e.value for e in EProviderName]}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Gọi application layer
        try:
            app_request = ISendMessageApplicationRequest(
                conversation_id=conversation_id,
                message=content,
                provider=provider,
                model_name=model_name,
                type=pipeline_type,
            )
            response = _run_application.send_message(app_request)

            return Response(
                {
                    "message": response.message,
                    "used_mock": response.used_mock,
                    "conversation_id": response.conversation_id,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
