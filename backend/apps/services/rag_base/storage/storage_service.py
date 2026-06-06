from pathlib import Path

from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.services.rag_base.storage.i_get_file_response import (
    IGetFileResponse,
)
from backend.apps.core.interfaces.services.rag_base.storage.i_storage import (
    IFileStorage,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_uploader import ILLMUploader
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.enums.e_mime_type import EMimeType
from backend.apps.utils.is_path_valiable import (
    check_file_path,
    check_storage_dir_exists_and_accessible,
)
from backend.apps.utils.mime_type import get_dir_by_mime_type, get_mime_type_from_path


class FileStorageService(IFileStorage):
    def __init__(
        self,
        storage_dir: Path,
        uploader: ILLMUploader,
        logger: ILogger,
    ):
        self.logger = logger
        self.storage_dir = storage_dir
        self.uploader = uploader
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_path: Path) -> ICreateFileResponse:
        new_file_path = self.__check_all(file_path=file_path)
        return self.uploader.upload_file(new_file_path)

    def load_file(self, file_info: ICreateFileResponse) -> IGetFileResponse:
        return self.uploader.load_file(file_info)

    def delete_file(self, file_id: str) -> bool:
        return self.uploader.delete_file(file_id)
    
    def is_file_existed(self, file_id: str) -> IGetFileResponse:
        return self.uploader.is_file_exists(file_id)


    # This method is to get file size in bytes, which can be used for logging, validation, etc.
    def get_file_size(self, file_info: ICreateFileResponse) -> float:
        return float(file_info.size_bytes)

    def __check_and_move_file_to_storage_dir(
        self, mime_type: EMimeType, file_path: Path
    ) -> Path:
        # check file_path is within storage_dir or not ? if not move this file to storage_dir
        if not self.storage_dir in file_path.parents:
            try:
                return self.__move_file_to_storage_dir(mime_type, file_path)
            except Exception as e:
                self.logger.error(
                    f"Error moving file to storage directory: {e}. This will fallback to copying the file to storage directory.",
                    source=str(self.__class__),
                )
                return self.__copy_file_to_storage_dir(mime_type, file_path)
        return file_path

    def __copy_file_to_storage_dir(self, mime_type: EMimeType, file_path: Path) -> Path:
        base_dir = get_dir_by_mime_type(self.storage_dir, mime_type, self.logger)
        base_dir.mkdir(parents=True, exist_ok=True)

        destination_path = base_dir / file_path.name
        if destination_path.exists():
            self.logger.warning(
                f"File '{destination_path}' already exists in storage directory. It will be overwritten.",
                source=str(self.__class__),
            )
        with file_path.open("rb") as src_file, destination_path.open("wb") as dst_file:
            dst_file.write(src_file.read())
        self.logger.info(
            f"Copied file '{file_path}' to storage directory '{self.storage_dir}'",
            source=str(self.__class__),
        )
        return destination_path

    def __move_file_to_storage_dir(self, mime_type: EMimeType, file_path: Path) -> Path:
        base_dir = get_dir_by_mime_type(self.storage_dir, mime_type, self.logger)
        base_dir.mkdir(parents=True, exist_ok=True)

        destination_path = base_dir / file_path.name
        if destination_path.exists():
            self.logger.warning(
                f"File '{destination_path}' already exists in storage directory. It will be overwritten.",
                source=str(self.__class__),
            )
        file_path.rename(destination_path)
        self.logger.info(
            f"Moved file '{file_path}' to storage directory '{self.storage_dir}'",
            source=str(self.__class__),
        )
        return destination_path

    def __check_all(self, file_path: Path) -> Path:
        check_file_path(file_path, self.logger)
        check_storage_dir_exists_and_accessible(self.storage_dir, self.logger)
        mime_type = get_mime_type_from_path(file_path)
        return self.__check_and_move_file_to_storage_dir(mime_type, file_path)
