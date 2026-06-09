from enum import Enum


class JobType(Enum):
    """Enumeration of available job types."""

    DOCUMENT_UPLOAD = "document_upload"
    MESSAGE_PROCESS = "message_process"
    CONVERSATION_PREPARE = "conversation_prepare"
    DELETE_CONVERSATION = "delete_conversation"
