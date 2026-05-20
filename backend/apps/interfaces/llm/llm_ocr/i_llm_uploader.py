"""
Mistral uploader interface module.
Abstract interface for uploading files to Mistral.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.apps.interfaces.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.interfaces.storage.i_get_file_response import IGetFileResponse


class ILLMUploader(ABC):
    """
    Abstract interface for Mistral file uploader.
    """

    @abstractmethod
    async def upload_file(self, file_path: Path) -> ICreateFileResponse:
        """
        Upload a file to Mistral and return the upload response.
        """
        pass

    @abstractmethod
    async def load_file(self, file_info: ICreateFileResponse) -> IGetFileResponse:
        """
        Load file content metadata from Mistral.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete file in Mistral.
        """
        pass
