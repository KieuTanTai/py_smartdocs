from pathlib import Path
from typing import cast

from mistralai.client import Mistral

from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_uploader import ILLMUploader
from backend.apps.core.interfaces.services.rag_base.storage.i_get_file_response import IGetFileResponse
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from backend.apps.core.interfaces.system.i_logging import ILogger


class MistralUploader(ILLMUploader):
    def __init__(self, logger: ILogger):
        self.logger = logger
        self.client = Mistral(api_key=MISTRAL_CONFIG["api_key"])

    def upload_file(self, file_path: Path) -> ICreateFileResponse:
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

    def load_file(self, file_id: str) -> IGetFileResponse:
        if file_id is None or file_id.strip() == "":
            message = "File id is missing for load_file."
            self.logger.error(message, source=str(self.__class__))
            raise ValueError(message)
        return self.__is_file_exists(file_id)

    def delete_file(self, file_id: str) -> bool:
        if not file_id:
            message = "File id is missing for delete_file."
            self.logger.error(message, source=str(self.__class__))
            raise ValueError(message)
        try:
            delete_response = self.client.files.delete(file_id=file_id)
            self.logger.info(
                f"Deleted file in Mistral: '{file_id}'",
                source=str(self.__class__),
            )
            return delete_response.deleted
        except Exception as e:
            self.logger.error(
                f"Failed to delete file in Mistral: '{file_id}'. Error: {e}",
                source=str(self.__class__),
            )
            raise e

    def __is_file_exists(self, file_id: str) -> IGetFileResponse:
        try:
            response = self.client.files.retrieve(file_id=file_id)
            self.logger.info(f"File with id '{file_id}' exists in Mistral",
                source=Path(__file__).name, call_by=str(self.__is_file_exists.__name__), method_call="retrieve")
            res = cast(IGetFileResponse, response)
            return res
        except Exception as e:
            self.logger.info(f"File with id '{file_id}' does not exist in Mistral. Error: {e}",
                source=Path(__file__).name, call_by=str(self.__is_file_exists.__name__), method_call="retrieve")
            raise FileNotFoundError(f"File with id '{file_id}' does not exist in Mistral. Error: {e}")