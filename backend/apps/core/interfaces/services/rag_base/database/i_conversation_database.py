"""
Conversation database service interface.
Defines conversation-specific CRUD behavior for ConversationModel.
"""

from abc import abstractmethod
from typing import Any

from django.db.models import QuerySet

from backend.apps.core.interfaces.services.rag_base.database.i_model_database import (
    IModelDatabase,
)
from backend.apps.services.chat.models import ConversationModel, DocumentModel


class IConversationDatabase(IModelDatabase[ConversationModel]):
    """Abstract database service for ConversationModel."""

    @abstractmethod
    def get_all(self) -> QuerySet[ConversationModel]:
        """Retrieve all conversations."""
        pass

    @abstractmethod
    def create_conversation(
        self,
        conversations_name: str = "",
        conversations_title: str = "",
        document: DocumentModel | None = None,
        **extra_fields: Any,
    ) -> ConversationModel:
        """Create a conversation, optionally linked to one document."""
        pass

    @abstractmethod
    def get_by_name(self, conversations_name: str) -> QuerySet[ConversationModel]:
        """Get conversations by conversation name."""
        pass

    @abstractmethod
    def get_by_document(self, document: DocumentModel) -> QuerySet[ConversationModel]:
        """Get conversations linked to the given document."""
        pass

    @abstractmethod
    def update_title(
        self, conversations_id: Any, conversations_title: str
    ) -> ConversationModel:
        """Update conversation title."""
        pass
