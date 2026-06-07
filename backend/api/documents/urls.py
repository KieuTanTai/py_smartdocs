from django.urls import path

from backend.api.documents.views import (
    DocumentListView,
    DocumentUploadView,
    DocumentDetailView,
    DocumentStatusView,
    DocumentIndexView,
    DocumentBulkIndexView,
)

urlpatterns = [
    path("", DocumentListView.as_view(), name="documents-list"),
    path("upload/", DocumentUploadView.as_view(), name="documents-upload"),
    path("<str:document_id>/", DocumentDetailView.as_view(), name="documents-detail"),
    path("<str:document_id>/status/", DocumentStatusView.as_view(), name="documents-status"),
    path("<str:document_id>/index/", DocumentIndexView.as_view(), name="documents-index"),
    path("index/bulk/", DocumentBulkIndexView.as_view(), name="documents-index-bulk"),
]
