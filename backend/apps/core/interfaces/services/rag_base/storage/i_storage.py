"""
Document storage interface module.
Abstract interface for file storage operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.services.rag_base.storage.i_get_file_response import (
    IGetFileResponse,
)


class IFileStorage(ABC):
    """
    Abstract interface for file storage.
    Handles file persistence (local filesystem or cloud).
    """

    @abstractmethod
    def save_file(self, file_path: Path) -> ICreateFileResponse:
        """
        Save uploaded file to storage.

        Args:
            file_path: Path to the file to save
            document_name: Name of the document

        Returns:
            ICreateFileResponse: Response object with file information
        """
        pass

    @abstractmethod
    def load_file(self, file_info: ICreateFileResponse) -> IGetFileResponse:
        """
        Load file content from storage.

        Args:
            file_info: File response info from upload cloud

        Returns:
            IGetFileResponse: Response object with file content or None if not found
        """
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_id: File id in upload cloud

        Returns:
            bool: True if file was deleted, False otherwise
        """
        pass

    @abstractmethod
    def get_file_size(self, file_info: ICreateFileResponse) -> float:
        """
        Get file size in bytes.

        Args:
            file_info: File response info from upload cloud

        Returns:
            File size in bytes
        """
        pass

    @abstractmethod
    def is_file_existed(self, file_id: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_id: File id in upload cloud

        Returns:
            bool: True if file exists, False otherwise
        """
        pass

    
