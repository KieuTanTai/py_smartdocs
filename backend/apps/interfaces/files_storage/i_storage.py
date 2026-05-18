"""
Document storage interface module.
Abstract interface for file storage operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.interfaces.files_storage.i_create_file_response import (
    ICreateFileResponse,
)
from sys_services.enums.e_mime_type import EMimeType


class IFileStorage(ABC):
    """
    Abstract interface for file storage.
    Handles file persistence (local filesystem or cloud).
    """

    @abstractmethod
    async def save_file(self, mime_type: EMimeType, file_path: Path) -> ICreateFileResponse:
        """
        Save uploaded file to storage.

        Args:
            mime_type: MIME type of the file
            file_path: Path to the file to save
            document_name: Name of the document

        Returns:
            ICreateFileResponse: Response object with file information
        """
        pass

    @abstractmethod
    async def load_file(self, mime_type: EMimeType, file_path: Path):
        """
        Load file content from storage.

        Args:
            mime_type: MIME type of the file
            file_path: Path to file in storage

        Returns:
            ICreateFileResponse: Response object with file content
        """
        pass

    @abstractmethod
    async def delete_file(self, mime_type: EMimeType, file_path: Path):
        """
        Delete file from storage.

        Args:
            mime_type: MIME type of the file
            file_path: Path to file in storage

        Returns:
            ICreateFileResponse: Response object with deletion information
        """
        pass

    @abstractmethod
    def get_file_size(self, mime_type: EMimeType, file_path: Path) -> float:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file in storage

        Returns:
            File size in bytes
        """
        pass
