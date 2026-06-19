"""
Message database service interface.
Defines CRUD behavior for MessageModel.
"""

from abc import abstractmethod
from typing import Any

from django.db.models import QuerySet

from backend.apps.core.interfaces.services.rag_base.database.i_model_database import (
    IModelDatabase,
)
from backend.apps.services.chat.models import ConversationModel, MessageModel


class IMessageDatabase(IModelDatabase[MessageModel]):
    """Abstract database service for MessageModel."""

    @abstractmethod
    def create_message(
        self,
        conversation: ConversationModel,
        content: str,
        is_user_send: bool,
        **extra_fields: Any,
    ) -> MessageModel:
        """Create a message for a conversation."""
        pass

    @abstractmethod
    def get_by_conversation(
        self, conversation: ConversationModel
    ) -> QuerySet[MessageModel]:
        """Get all messages attached to the given conversation."""
        pass

    @abstractmethod
    def get_user_messages(
        self, conversation: ConversationModel
    ) -> QuerySet[MessageModel]:
        """Get user-sent messages for the given conversation."""
        pass

    @abstractmethod
    def get_assistant_messages(
        self, conversation: ConversationModel
    ) -> QuerySet[MessageModel]:
        """Get assistant/system messages for the given conversation."""
        pass

    @abstractmethod
    def delete_by_conversation(self, conversation: ConversationModel) -> int:
        """Delete all messages attached to the given conversation."""
        pass
