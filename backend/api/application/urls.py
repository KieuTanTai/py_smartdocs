from django.urls import path

from backend.api.application.views import (
    ApplicationUploadView,
    ApplicationConversationListView,
    ApplicationConversationView,
    ApplicationMessageView,
)

urlpatterns = [
    # Upload files + tạo conversation + chạy pipeline
    path("upload/", ApplicationUploadView.as_view(), name="app-upload"),

    # List all conversations
    path("conversations/", ApplicationConversationListView.as_view(), name="app-conversations"),

    # Get/Delete single conversation
    path("conversations/<str:conversation_id>/", ApplicationConversationView.as_view(), name="app-conversation-detail"),

    # Send message (RAG + LLM)
    path("conversations/<str:conversation_id>/messages/", ApplicationMessageView.as_view(), name="app-messages"),
]
