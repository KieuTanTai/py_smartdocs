"""
Conversation file database service interface.
Defines CRUD behavior for ConversationFilesModel.
"""

from abc import abstractmethod
from typing import Any

from django.db.models import QuerySet

from backend.apps.core.interfaces.services.rag_base.database.i_model_database import (
    IModelDatabase,
)
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, DocumentModel


class IConversationFileDatabase(IModelDatabase[ConversationFilesModel]):
    """Abstract database service for ConversationFilesModel."""

    @abstractmethod
    def create_conversation_file(
        self,
        document: DocumentModel,
        cloud_id: str,
        **extra_fields: Any,
    ) -> ConversationFilesModel:
        """Create a file link for a document."""
        pass

    @abstractmethod
    def create_conversation_files_bulk(
        self,
        document_cloud_id_pairs: list[tuple[DocumentModel, str]],
        **extra_fields: Any,
    ) -> list[ConversationFilesModel]:
        """Bulk create file links for multiple documents."""
        pass

    @abstractmethod
    def get_by_document(
        self, document: DocumentModel
    ) -> QuerySet[ConversationFilesModel]:
        """Get file links attached to the given document."""
        pass

    @abstractmethod
    def get_by_cloud_id(self, cloud_id: str) -> QuerySet[ConversationFilesModel]:
        """Get file links by stored cloud/document id."""
        pass

    @abstractmethod
    def get_by_cloud_ids(self, cloud_ids: list[str]) -> QuerySet[ConversationFilesModel]:
        """Get multiple conversation file instances by cloud IDs."""
        pass

    @abstractmethod
    def delete_by_document(self, document: DocumentModel) -> int:
        """Delete all file links attached to the given document."""
        pass

    @abstractmethod
    def get_by_conversation(self, conversation: ConversationModel) -> QuerySet[ConversationFilesModel]:
        """Get file links attached to the given conversation."""
        pass