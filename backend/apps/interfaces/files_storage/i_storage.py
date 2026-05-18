"""
Document storage interface module.
Abstract interface for file storage operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.interfaces.files_storage.i_create_file_response import (
    ICreateFileResponse,
)


class IFileStorage(ABC):
    """
    Abstract interface for file storage.
    Handles file persistence (local filesystem or cloud).
    """

    @abstractmethod
    async def save_file(self, file_path: Path) -> ICreateFileResponse:
        """
        Save uploaded file to storage.

        Args:
            file_obj: File object from upload
            document_name: Name of the document

        Returns:
            ICreateFileResponse: Response object with file information
        """
        pass

    @abstractmethod
    async def load_file(self, file_path: Path):
        """
        Load file content from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            ICreateFileResponse: Response object with file content
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: Path):
        """
        Delete file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            ICreateFileResponse: Response object with deletion information
        """
        pass

    @abstractmethod
    def get_file_size(self, file_path: Path) -> float:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file in storage

        Returns:
            File size in bytes
        """
        pass
