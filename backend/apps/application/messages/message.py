"""
Message module.
Manages message entities and chat history.
"""


class Message:
    """
    Represents a single message in a conversation.

    Attributes:
        id: Unique identifier
        conversation_id: Reference to parent conversation
        role: Message origin ('system', 'user', 'assistant')
        content: Message text content
        provider: LLM provider used (if assistant role)
        model: Model identifier used (if assistant role)
        tokens_input: Input tokens consumed (if assistant role)
        tokens_output: Output tokens generated (if assistant role)
        latency_ms: Response latency in milliseconds (if assistant role)
        metadata_json: Additional metadata (retrieval context, etc.)
        created_at: Timestamp of creation
    """

    def __init__(self):
        # TODO: Initialize message attributes
        pass

    def is_user_message(self):
        # TODO: Check if message is from user
        pass

    def is_assistant_message(self):
        # TODO: Check if message is from assistant
        pass

    def get_metadata(self):
        # TODO: Parse and return metadata JSON
        pass
