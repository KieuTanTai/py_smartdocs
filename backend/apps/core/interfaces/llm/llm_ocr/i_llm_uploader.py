"""
Mistral uploader interface module.
Abstract interface for uploading files to Mistral.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.services.rag_base.storage.i_get_file_response import IGetFileResponse


class ILLMUploader(ABC):
    """
    Abstract interface for Mistral file uploader.
    """

    @abstractmethod
    def upload_file(self, file_path: Path) -> ICreateFileResponse:
        """
        Upload a file to Mistral and return the upload response.
        """
        pass

    @abstractmethod
    def load_file(self, file_info: ICreateFileResponse) -> IGetFileResponse:
        """
        Load file content metadata from Mistral.
        """
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file in Mistral.
        """
        pass

    @abstractmethod
    def is_file_exists(self, file_id: str) -> bool:
        """
        Check if file exists in Mistral.
        """
        pass