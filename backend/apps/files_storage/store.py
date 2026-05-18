import os
from pathlib import Path

from backend.apps.interfaces.files_storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.interfaces.files_storage.i_storage import IFileStorage
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER


class FileStorage(IFileStorage):
    def __init__(self, storage_dir: Path, logger: ILogger | None):
        self.logger = logger or DEFAULT_LOGGER
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_path: Path) -> ICreateFileResponse:
        new_file_path = self.__check_all(file_path)

    async def load_file(self, file_path: Path):
        # Implement file loading logic (e.g., read from local filesystem or cloud storage)
        pass

    async def delete_file(self, file_path: Path):
        # Implement file deletion logic (e.g., delete from local filesystem or cloud storage)
        pass

    def get_file_size(self, file_path: Path) -> float:
        # Implement logic to get file size in bytes
        pass

    def __check_and_move_file_to_storage_dir(self, file_path: Path) -> Path:
        # check file_path is within storage_dir or not ? if not move this file to storage_dir
        if not self.storage_dir in file_path.parents:
            try:
                return self.__move_file_to_storage_dir(file_path)
            except Exception as e:
                self.logger.error(
                    f"Error moving file to storage directory: {e}. This will fallback to copying the file to storage directory.",
                    source=str(self.__class__),
                )
                return self.__copy_file_to_storage_dir(file_path)
        return file_path

    def __check_all(self, file_path: Path) -> Path:
        self.__check_file_exists(file_path)
        self.__check_storage_dir_exists_and_accessible()
        return self.__check_and_move_file_to_storage_dir(file_path)

    def __check_file_exists(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self.logger.error(
                f"File not found: {file_path}", source=str(self.__class__)
            )
            raise ValueError(f"File not found: {file_path}")

    def __check_storage_dir_exists_and_accessible(self):
        if not os.path.exists(self.storage_dir):
            self.logger.error(
                f"Storage directory does not exist: {self.storage_dir}",
                source=str(self.__class__),
            )
            raise FileNotFoundError(
                f"Storage directory does not exist: {self.storage_dir}"
            )

        if not os.access(self.storage_dir, os.W_OK | os.R_OK):
            self.logger.error(
                f"Storage directory is not accessible: {self.storage_dir}",
                source=str(self.__class__),
            )
            raise PermissionError(
                f"Storage directory is not accessible: {self.storage_dir}"
            )

    def __copy_file_to_storage_dir(self, file_path: Path) -> Path:
        destination_path = self.storage_dir / file_path.name
        with file_path.open("rb") as src_file, destination_path.open("wb") as dst_file:
            dst_file.write(src_file.read())
        self.logger.info(
            f"Copied file {file_path} to storage directory {self.storage_dir}",
            source=str(self.__class__),
        )
        return destination_path

    def __move_file_to_storage_dir(self, file_path: Path) -> Path:
        destination_path = self.storage_dir / file_path.name
        file_path.rename(destination_path)
        self.logger.info(
            f"Moved file {file_path} to storage directory {self.storage_dir}",
            source=str(self.__class__),
        )
        return destination_path
