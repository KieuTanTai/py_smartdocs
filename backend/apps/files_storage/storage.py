import os
from pathlib import Path

from backend.apps.interfaces.files_storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.interfaces.files_storage.i_storage import IFileStorage
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER
from sys_services.enums.e_mime_type import MimeType


class FileStorage(IFileStorage):
    def __init__(self, storage_dir: Path, logger: ILogger | None):
        self.logger = logger or DEFAULT_LOGGER
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, mime_type: MimeType, file_path: Path) -> ICreateFileResponse:
        new_file_path = self.__check_all(mime_type=mime_type, file_path=file_path)

    async def load_file(self, mime_type: MimeType, file_path: Path):
        # Implement file loading logic (e.g., read from local filesystem or cloud storage)
        pass

    async def delete_file(self, mime_type: MimeType, file_path: Path):
        # Implement file deletion logic (e.g., delete from local filesystem or cloud storage)
        pass

    def get_file_size(self, mime_type: MimeType, file_path: Path) -> float:
        # Implement logic to get file size in bytes
        pass

    def __check_and_move_file_to_storage_dir(self, mime_type: MimeType, file_path: Path) -> Path:
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

    def __copy_file_to_storage_dir(self, mime_type: MimeType, file_path: Path) -> Path:
        base_dir = self.__get_dir_by_mime_type(mime_type)
        base_dir.mkdir(parents=True, exist_ok=True)

        destination_path = base_dir / file_path.name
        if (destination_path.exists()):
            self.logger.warning(
                f"File {destination_path} already exists in storage directory. It will be overwritten.",
                source=str(self.__class__),
            )
        with file_path.open("rb") as src_file, destination_path.open("wb") as dst_file:
            dst_file.write(src_file.read())
        self.logger.info(
            f"Copied file {file_path} to storage directory {self.storage_dir}",
            source=str(self.__class__),
        )
        return destination_path

    def __move_file_to_storage_dir(self, mime_type: MimeType, file_path: Path) -> Path:
        base_dir = self.__get_dir_by_mime_type(mime_type)
        base_dir.mkdir(parents=True, exist_ok=True)

        destination_path = base_dir / file_path.name
        if (destination_path.exists()):
            self.logger.warning(
                f"File {destination_path} already exists in storage directory. It will be overwritten.",
                source=str(self.__class__),
            )
        file_path.rename(destination_path)
        self.logger.info(
            f"Moved file {file_path} to storage directory {self.storage_dir}",
            source=str(self.__class__),
        )
        return destination_path

    def __check_all(self, mime_type: MimeType, file_path: Path) -> Path:
        self.__check_file_exists(file_path)
        self.__check_storage_dir_exists_and_accessible()
        return self.__check_and_move_file_to_storage_dir(mime_type, file_path)

    def __check_file_exists(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self.logger.error(
                f"File not found: {file_path}", source=str(self.__class__)
            )
            raise ValueError(f"File not found: {file_path}")

    def __check_storage_dir_exists_and_accessible(self):
        if not os.path.exists(self.storage_dir):
            self.logger.warning(
                f"Storage directory does not exist: {self.storage_dir} and will be created.",
                source=str(self.__class__),
            )
            os.makedirs(self.storage_dir, exist_ok=True)

        if not os.access(self.storage_dir, os.W_OK | os.R_OK):
            self.logger.error(
                f"Storage directory is not accessible: {self.storage_dir}",
                source=str(self.__class__),
            )
            raise PermissionError(
                f"Storage directory is not accessible: {self.storage_dir}"
            )

    def __get_dir_by_mime_type(self, mime_type: MimeType) -> Path:
        if (mime_type == MimeType.PDF):
            return self.storage_dir / "pdf"
        elif (mime_type == MimeType.DOCX):
            return self.storage_dir / "docx"
        elif (mime_type == MimeType.TXT):
            return self.storage_dir / "txt"
        elif (mime_type == MimeType.JPEG):
            return self.storage_dir / "images" / "jpeg"
        elif (mime_type == MimeType.PNG):
            return self.storage_dir / "images" / "png"
        elif (mime_type == MimeType.JPG):
            return self.storage_dir / "images" / "jpg"
        elif (mime_type == MimeType.TIFF):
            return self.storage_dir / "images" / "tiff"
        else:
            self.logger.error(
                f"Unsupported MIME type: {mime_type}",
                source=str(self.__class__),
            )
            raise ValueError(f"Unsupported MIME type: {mime_type}")
