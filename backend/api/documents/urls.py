from django.urls import path

from backend.api.documents.views import (
    DocumentListView,
    DocumentUploadView,
    ConversationListView,
    MessageListViewByConversation
)

urlpatterns = [
    # Specific routes MUST come before the catch-all "" to avoid 405 errors
    path("upload/", DocumentUploadView.as_view(), name="documents-upload"),
    # Catch-all (list/create) must be last
    path("", DocumentListView.as_view(), name="documents-list"),
    path("conversation/", ConversationListView.as_view(), name="conversation-list"),
    path("message/", MessageListViewByConversation.as_view(), name="message-list"),
]
