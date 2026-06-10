"""
Custom exception definitions.
Domain-specific exceptions for error handling.
"""


from backend.apps.core.interfaces.exception.i_smartdocs_exception import ISmartdocsException


class DocumentsNotReadyError(ISmartdocsException):
    """
    Raised when documents are not ready for processing.
    """
    def __init__(self, message: str = "Documents are not ready for processing.", error_code: str | None = None):
        super().__init__(message, error_code)
        self.error_code = error_code
        super().__init__(message)


class DocumentProcessingError(ISmartdocsException):
    """
    Raised when document processing fails.
    """

    pass


class EmbeddingError(ISmartdocsException):
    """
    Raised when embedding generation fails.
    """

    pass


class VectorStoreError(ISmartdocsException):
    """
    Raised when vector store operations fail.
    """

    pass


class LLMProviderError(ISmartdocsException):
    """
    Raised when LLM provider call fails.
    """

    pass


class ConversationError(ISmartdocsException):
    """
    Raised when conversation operations fail.
    """

    pass


class FileExtractionError(ISmartdocsException):
    """
    Raised when file extraction fails.
    """

    pass
