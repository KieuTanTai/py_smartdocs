"""
Mistral uploader interface module.
Abstract interface for uploading files to Mistral.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.apps.interfaces.files_storage.i_create_file_response import (
    ICreateFileResponse,
)


class IMistralUploader(ABC):
    """
    Abstract interface for Mistral file uploader.
    """

    @abstractmethod
    async def upload_file(self, file_path: Path) -> ICreateFileResponse:
        """
        Upload a file to Mistral and return the upload response.
        """
        pass
