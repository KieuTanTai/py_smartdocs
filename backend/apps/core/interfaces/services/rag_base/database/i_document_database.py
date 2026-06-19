"""
Document database service interface.
Defines document-specific CRUD behavior for DocumentModel.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any

from django.db.models import QuerySet

from backend.apps.core.enums.e_document_status import EDocumentStatus
from backend.apps.core.interfaces.services.rag_base.database.i_model_database import (
    IModelDatabase,
)
from backend.apps.services.chat.models import DocumentModel


class IDocumentDatabase(IModelDatabase[DocumentModel]):
    """Abstract database service for DocumentModel."""

    @abstractmethod
    def create_document(
        self,
        # faiss_index_file_name: str,
        file_path: str | Path | None = None,
        status: EDocumentStatus = EDocumentStatus.UPLOADED,
        content: str | None = None,
        is_active: bool = True,
        **extra_fields: Any,
    ) -> DocumentModel:
        """Create a document with the fields used by the upload pipeline."""
        pass

    # @abstractmethod
    # def get_by_file_name(self, faiss_index_file_name: str) -> QuerySet[DocumentModel]:
    #     """Get documents by FAISS index file name."""
    #     pass

    @abstractmethod
    def update_status(self, document_id: Any, status: EDocumentStatus) -> DocumentModel:
        """Update document processing status."""
        pass

    @abstractmethod
    def deactivate(self, document_id: Any) -> DocumentModel:
        """Mark a document as inactive without deleting it."""
        pass
