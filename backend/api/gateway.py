"""
API gateway.

Skeleton endpoints for the core API surface.
"""

from __future__ import annotations

from django.urls import path
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class HealthView(APIView):
    def get(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class ProviderListView(APIView):
    def get(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class ProviderTestView(APIView):
    def post(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class DocumentListView(APIView):
    def get(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class DocumentUploadView(APIView):
    def post(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class DocumentDetailView(APIView):
    def get(self, request, document_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )

    def delete(self, request, document_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class DocumentStatusView(APIView):
    def get(self, request, document_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class DocumentIndexView(APIView):
    def post(self, request, document_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class DocumentBulkIndexView(APIView):
    def post(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class ConversationListView(APIView):
    def get(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )

    def post(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class ConversationDetailView(APIView):
    def get(self, request, conversation_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class ConversationStatusView(APIView):
    def get(self, request, conversation_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class ConversationDocumentsView(APIView):
    def patch(self, request, conversation_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class MessageListView(APIView):
    def get(self, request, conversation_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )

    def post(self, request, conversation_id: str):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


class CoreSearchView(APIView):
    def post(self, request):
        return Response(
            {"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED
        )


urlpatterns = [
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/providers/", ProviderListView.as_view(), name="providers"),
    path("api/providers/test/", ProviderTestView.as_view(), name="providers-test"),
    path("api/documents/", DocumentListView.as_view(), name="documents-list"),
    path(
        "api/documents/upload/", DocumentUploadView.as_view(), name="documents-upload"
    ),
    path(
        "api/documents/<str:document_id>/",
        DocumentDetailView.as_view(),
        name="documents-detail",
    ),
    path(
        "api/documents/<str:document_id>/status/",
        DocumentStatusView.as_view(),
        name="documents-status",
    ),
    path(
        "api/documents/<str:document_id>/index/",
        DocumentIndexView.as_view(),
        name="documents-index",
    ),
    path(
        "api/documents/index/bulk/",
        DocumentBulkIndexView.as_view(),
        name="documents-index-bulk",
    ),
    path("api/conversations/", ConversationListView.as_view(), name="conversations"),
    path(
        "api/conversations/<str:conversation_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "api/conversations/<str:conversation_id>/status/",
        ConversationStatusView.as_view(),
        name="conversation-status",
    ),
    path(
        "api/conversations/<str:conversation_id>/documents/",
        ConversationDocumentsView.as_view(),
        name="conversation-documents",
    ),
    path(
        "api/conversations/<str:conversation_id>/messages/",
        MessageListView.as_view(),
        name="messages",
    ),
    path(
        "api/application/conversations/",
        ConversationListView.as_view(),
        name="app-conversations",
    ),
    path(
        "api/application/conversations/<str:conversation_id>/",
        ConversationDetailView.as_view(),
        name="app-conversation-detail",
    ),
    path(
        "api/application/conversations/<str:conversation_id>/status/",
        ConversationStatusView.as_view(),
        name="app-conversation-status",
    ),
    path(
        "api/application/conversations/<str:conversation_id>/documents/",
        ConversationDocumentsView.as_view(),
        name="app-conversation-documents",
    ),
    path(
        "api/application/conversations/<str:conversation_id>/messages/",
        MessageListView.as_view(),
        name="app-messages",
    ),
    path("api/core/search/", CoreSearchView.as_view(), name="core-search"),
]
