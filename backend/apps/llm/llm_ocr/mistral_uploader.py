from pathlib import Path

from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_uploader import ILLMUploader
from backend.apps.core.interfaces.services.rag_base.storage.i_get_file_response import IGetFileResponse
from mistralai.client import Mistral, cast
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

    def load_file(self, file_info: ICreateFileResponse) -> IGetFileResponse:
        file_id = getattr(file_info, "id", None)
        if not file_id:
            message = "File id is missing for load_file."
            self.logger.error(message, source=str(self.__class__))
            raise ValueError(message)

        metadata_path = Path("media") / "metadata" / f"{file_id}.md"
        if not metadata_path.exists():
            message = f"Metadata file not found: '{metadata_path}'"
            self.logger.error(message, source=str(self.__class__))
            raise FileNotFoundError(message)

        try:
            stored_path = metadata_path.read_text(encoding="utf-8").strip()
            if not stored_path:
                self.logger.warning(
                    f"Metadata file is empty: '{metadata_path}'",
                    source=str(self.__class__),
                )

            retrieved_file = self.client.files.retrieve(file_id=file_id)
            self.logger.info(
                f"Retrieved file from Mistral: '{file_id}' (stored path: '{stored_path}')",
                source=str(self.__class__),
            )
            return cast(IGetFileResponse, retrieved_file)
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve file: '{file_id}'. Error: {e}",
                source=str(self.__class__),
            )
            raise e

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

    def is_file_exists(self, file_id: str) -> bool:
        try:
            self.client.files.retrieve(file_id=file_id)
            self.logger.info(f"File with id '{file_id}' exists in Mistral",
                Path(__file__).name, Path(__file__).name)
            return True
        except Exception as e:
            self.logger.info(f"File with id '{file_id}' does not exist in Mistral. Error: {e}",
                Path(__file__).name, Path(__file__).name)
            return False