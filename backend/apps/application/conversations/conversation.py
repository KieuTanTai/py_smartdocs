"""
Conversation module.
Manages conversation entities, state transitions, and document attachments.
"""


class Conversation:
    """
    Represents a conversation session.

    Attributes:
        id: Unique identifier
        title: Human-readable conversation title
        provider: LLM provider name (e.g., 'gemini', 'ollama')
        model: Model identifier for the selected provider
        system_prompt: Custom system instruction for the conversation
        status: Current state ('preparing', 'ready', 'failed')
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    def __init__(self):
        # TODO: Initialize conversation attributes
        pass

    def add_document(self, document_id):
        # TODO: Attach a document to this conversation
        pass

    def remove_document(self, document_id):
        # TODO: Detach a document from this conversation
        pass

    def set_status(self, status):
        # TODO: Update conversation status with validation
        pass

    def is_ready(self):
        # TODO: Check if conversation is ready for chat
        pass


class ConversationDocument:
    """
    Many-to-many join table between Conversation and Document.
    Tracks document relationships within conversations.
    """

    def __init__(self):
        # TODO: Initialize conversation-document relationship
        pass
