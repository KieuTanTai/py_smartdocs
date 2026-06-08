"""
Chat views - Delegation layer.

All endpoints are implemented in backend.api.conversations.views.
This module exists for backward compatibility and legacy reference.
"""

# Re-export real implementations so any remaining imports don't break.
from backend.api.conversations.views import (
    ConversationListView,
    ConversationDetailView,
    ConversationStatusView,
    ConversationDocumentsView,
    MessageListView,
)
from backend.api.documents.views import (
    DocumentListView,
    DocumentUploadView,
    DocumentDetailView,
    DocumentStatusView,
    DocumentIndexView,
    DocumentBulkIndexView,
)
