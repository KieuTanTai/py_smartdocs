from django.urls import path

from backend.api.conversations.views import (
    ConversationListView,
    ConversationDetailView,
    ConversationStatusView,
    ConversationDocumentsView,
    MessageListView,
)

urlpatterns = [
    path("", ConversationListView.as_view(), name="conversations"),
    path("<str:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("<str:conversation_id>/status/", ConversationStatusView.as_view(), name="conversation-status"),
    path("<str:conversation_id>/documents/", ConversationDocumentsView.as_view(), name="conversation-documents"),
    path("<str:conversation_id>/messages/", MessageListView.as_view(), name="messages"),
]
