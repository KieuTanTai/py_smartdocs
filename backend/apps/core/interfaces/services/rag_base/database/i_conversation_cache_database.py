"""
Document database service interface.
Defines document-specific CRUD behavior for ConversationCacheModel.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any

from django.db.models import QuerySet

from backend.apps.core.enums.e_document_status import EDocumentStatus
from backend.apps.core.interfaces.services.rag_base.database.i_model_database import (
    IModelDatabase,
)
from backend.apps.services.chat.models import ConversationCacheModel, ConversationModel


class IConversationCacheDatabase(IModelDatabase[ConversationCacheModel]):
    """Abstract database service for ConversationCacheModel."""

    @abstractmethod
    def create_conversation_cache(
        self,
        conversation: ConversationModel,
        file_path: Path | None = None,
        status: EDocumentStatus = EDocumentStatus.UPLOADED,
        content: str | None = None,
        is_active: bool = True,
        **extra_fields: Any,
    ) -> ConversationCacheModel:
        """Create a document with the fields used by the upload pipeline."""
        pass

    # @abstractmethod
    # def get_by_file_name(self, faiss_index_file_name: str) -> QuerySet[ConversationCacheModel]:
    #     """Get documents by FAISS index file name."""
    #     pass

    @abstractmethod
    def get_by_conversation(self, conversation: ConversationModel) -> ConversationCacheModel:
        """Get documents by conversation."""
        pass

    @abstractmethod
    def get_by_file_path(self, file_path: Path) -> QuerySet[ConversationCacheModel]:
        """Get documents by file path."""
        pass

    @abstractmethod
    def get_by_file_paths(self, file_paths: list[Path]) -> QuerySet[ConversationCacheModel]:
        """Get documents by multiple file paths."""
        pass

    @abstractmethod
    def update_status(self, document_id: Any, status: EDocumentStatus) -> ConversationCacheModel:
        """Update document processing status."""
        pass

    @abstractmethod
    def deactivate(self, document_id: Any) -> ConversationCacheModel:
        """Mark a document as inactive without deleting it."""
        pass
