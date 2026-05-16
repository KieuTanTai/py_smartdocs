"""
Custom exception definitions.
Domain-specific exceptions for error handling.
"""


class SmartDocsException(Exception):
    """
    Base exception for all SmartDocs application errors.
    """

    pass


class DocumentProcessingError(SmartDocsException):
    """
    Raised when document processing fails.
    """

    pass


class EmbeddingError(SmartDocsException):
    """
    Raised when embedding generation fails.
    """

    pass


class VectorStoreError(SmartDocsException):
    """
    Raised when vector store operations fail.
    """

    pass


class LLMProviderError(SmartDocsException):
    """
    Raised when LLM provider call fails.
    """

    pass


class ConversationError(SmartDocsException):
    """
    Raised when conversation operations fail.
    """

    pass


class FileExtractionError(SmartDocsException):
    """
    Raised when file extraction fails.
    """

    pass
