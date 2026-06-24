from django.urls import path

from backend.api.documents.views import (
    DocumentListView,
    DocumentUploadView,
    ConversationListView,
    MessageListViewByConversation,
    SendMesssage
)
# from backend.api.documents.bulk_index import DocumentBulkIndexView

urlpatterns = [
    # Specific routes MUST come before the catch-all "" to avoid 405 errors
    path("upload/", DocumentUploadView.as_view(), name="documents-upload"),
    # NOTE: "index/bulk/" MUST come BEFORE "<str:document_id>/" to avoid "index" being
    # captured as a document_id and returning 405 (wrong view: DocumentDetailView).
    # path("index/bulk/", DocumentBulkIndexView.as_view(), name="documents-index-bulk"),
    # Catch-all (list/create) must be last
    path("", DocumentListView.as_view(), name="documents-list"),
    path("conversation/", ConversationListView.as_view(), name="conversation-list"),
    path("message/", MessageListViewByConversation.as_view(), name=""),
    path("send_message/", SendMesssage.as_view(), name="send-message"),

]
