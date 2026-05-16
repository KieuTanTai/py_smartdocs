"""
Document storage interface module.
Abstract interface for file storage operations.
"""

from abc import ABC, abstractmethod


class DocumentStorageInterface(ABC):
    """
    Abstract interface for file storage.
    Handles file persistence (local filesystem or cloud).
    """

    @abstractmethod
    async def save_file(self, file_obj, document_id):
        """
        Save uploaded file to storage.

        Args:
            file_obj: File object from upload
            document_id: Associated document ID

        Returns:
            File path or storage identifier
        """
        pass

    @abstractmethod
    async def load_file(self, file_path):
        """
        Load file content from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path):
        """
        Delete file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            Boolean success status
        """
        pass

    @abstractmethod
    def get_file_size(self, file_path):
        """
        Get file size in bytes.

        Args:
            file_path: Path to file in storage

        Returns:
            File size in bytes
        """
        pass
