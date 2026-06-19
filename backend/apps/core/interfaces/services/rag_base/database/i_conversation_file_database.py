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
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel


class IConversationFileDatabase(IModelDatabase[ConversationFilesModel]):
    """Abstract database service for ConversationFilesModel."""

    @abstractmethod
    def create_conversation_file(
        self,
        conversation: ConversationModel,
        cloud_id: str,
        **extra_fields: Any,
    ) -> ConversationFilesModel:
        """Create a file link for a conversation."""
        pass

    @abstractmethod
    def get_by_conversation(
        self, conversation: ConversationModel
    ) -> QuerySet[ConversationFilesModel]:
        """Get file links attached to the given conversation."""
        pass

    @abstractmethod
    def get_by_cloud_id(self, cloud_id: str) -> QuerySet[ConversationFilesModel]:
        """Get file links by stored cloud/document id."""
        pass

    @abstractmethod
    def delete_by_conversation(self, conversation: ConversationModel) -> int:
        """Delete all file links attached to the given conversation."""
        pass
