"""
Conversation service interface module.
Abstract interface for conversation operations.
"""

from abc import ABC, abstractmethod


class ConversationServiceInterface(ABC):
    """
    Abstract interface for conversation operations.
    Manages conversation lifecycle and state.
    """

    @abstractmethod
    async def create_conversation(
        self, title, document_ids, provider, model, system_prompt=None
    ):
        """
        Create a new conversation.

        Args:
            title: Conversation title
            document_ids: List of attached document IDs
            provider: LLM provider name (e.g., 'gemini', 'ollama')
            model: Model identifier
            system_prompt: Optional custom system prompt

        Returns:
            Conversation object
        """
        pass

    @abstractmethod
    async def get_conversation(self, conversation_id):
        """
        Retrieve conversation details.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation object
        """
        pass

    @abstractmethod
    async def update_conversation_status(self, conversation_id, status):
        """
        Update conversation status.

        Args:
            conversation_id: Conversation ID
            status: New status ('preparing', 'ready', 'failed')

        Returns:
            Updated conversation object
        """
        pass

    @abstractmethod
    async def add_document_to_conversation(self, conversation_id, document_id):
        """
        Add document to conversation.

        Args:
            conversation_id: Conversation ID
            document_id: Document ID to attach

        Returns:
            Updated conversation object
        """
        pass
