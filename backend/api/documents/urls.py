from django.urls import path

from backend.api.documents.views import (
    DocumentListView,
    DocumentUploadView,
    DocumentDetailView,
    DocumentStatusView,
    DocumentIndexView,
)
from backend.api.documents.bulk_index import DocumentBulkIndexView

urlpatterns = [
    # Specific routes MUST come before the catch-all "" to avoid 405 errors
    path("upload/", DocumentUploadView.as_view(), name="documents-upload"),
    # NOTE: "index/bulk/" MUST come BEFORE "<str:document_id>/" to avoid "index" being
    # captured as a document_id and returning 405 (wrong view: DocumentDetailView).
    path("index/bulk/", DocumentBulkIndexView.as_view(), name="documents-index-bulk"),
    path("<str:document_id>/", DocumentDetailView.as_view(), name="documents-detail"),
    path("<str:document_id>/status/", DocumentStatusView.as_view(), name="documents-status"),
    path("<str:document_id>/index/", DocumentIndexView.as_view(), name="documents-index"),
    # Catch-all (list/create) must be last
    path("", DocumentListView.as_view(), name="documents-list"),
]
