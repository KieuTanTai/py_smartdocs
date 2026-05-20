"""
Document storage interface module.
Abstract interface for file storage operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from backend.apps.interfaces.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.interfaces.storage.i_get_file_response import IGetFileResponse
from sys_services.enums.e_mime_type import EMimeType


class IFileStorage(ABC):
    """
    Abstract interface for file storage.
    Handles file persistence (local filesystem or cloud).
    """

    @abstractmethod
    async def save_file(
        self, mime_type: EMimeType, file_path: Path
    ) -> ICreateFileResponse:
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
    async def load_file(self, file_info: ICreateFileResponse) -> IGetFileResponse:
        """
        Load file content from storage.

        Args:
            file_info: File response info from Mistral

        Returns:
            IGetFileResponse: Response object with file content or None if not found
        """
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_id: File id in Mistral

        Returns:
            bool: True if file was deleted, False otherwise
        """
        pass

    @abstractmethod
    def get_file_size(self, file_info: ICreateFileResponse) -> float:
        """
        Get file size in bytes.

        Args:
            file_info: File response info from Mistral

        Returns:
            File size in bytes
        """
        pass
