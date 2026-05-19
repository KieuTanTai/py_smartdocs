from pathlib import Path

from backend.apps.interfaces.files_storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.interfaces.files_storage.i_mistral_uploader import IMistralUploader
from mistralai.client import Mistral, cast
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER


class MistralUploader(IMistralUploader):
    def __init__(self, logger: ILogger | None = None):
        self.logger = logger or DEFAULT_LOGGER
        self.client = Mistral(api_key=MISTRAL_CONFIG["api_key"])

    async def upload_file(self, file_path: Path) -> ICreateFileResponse:
        try:
            with open(file_path, "rb") as file_handle:
                upload_response = self.client.files.upload(
                    file={
                        "file_name": file_path.name,
                        "content": file_handle,
                    },
                    purpose="ocr",
                )
            self.logger.info(
                f"Uploaded file to Mistral: '{file_path}'",
                source=str(self.__class__),
            )
            return cast(ICreateFileResponse, upload_response)
        except Exception as e:
            self.logger.error(
                f"Failed to upload file to Mistral: '{file_path}'. Error: {e}",
                source=str(self.__class__),
            )
            raise e
