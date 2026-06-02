"""
Message service interface module.
Abstract interface for message operations.
"""

from abc import ABC, abstractmethod


class IMessageService(ABC):
    """
    Abstract interface for message operations.
    Manages chat history and message persistence.
    """

    @abstractmethod
    def create_message(self, conversation_id, role, content, metadata=None):
        """
        Create and save a message.

        Args:
            conversation_id: Parent conversation ID
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata (retrieval context, provider info, tokens, etc.)

        Returns:
            Message object
        """
        pass

    @abstractmethod
    def get_conversation_history(self, conversation_id, limit=None):
        """
        Retrieve conversation message history.

        Args:
            conversation_id: Conversation ID
            limit: Optional limit on number of messages

        Returns:
            List of Message objects in chronological order
        """
        pass

    @abstractmethod
    def update_message(self, message_id, **fields):
        """
        Update message fields.

        Args:
            message_id: Message ID
            **fields: Fields to update (tokens_input, tokens_output, latency_ms, etc.)

        Returns:
            Updated message object
        """
        pass
