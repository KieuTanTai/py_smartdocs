"""
Storage module.
File storage abstraction for document files.
"""


class StorageService:
    """
    Abstract storage service for file management.
    Supports local filesystem and cloud storage.
    """

    def __init__(self):
        # TODO: Initialize storage service
        pass

    async def save_file(self, file_obj, document_id):
        # TODO: Save uploaded file
        # Returns: file path or identifier
        pass

    async def load_file(self, file_path):
        # TODO: Load file from storage
        # Returns: file content
        pass

    async def delete_file(self, file_path):
        # TODO: Delete file from storage
        pass

    def get_file_size(self, file_path):
        # TODO: Get file size in bytes
        pass


class LocalStorageService(StorageService):
    """
    Local filesystem storage implementation.
    """

    def __init__(self):
        # TODO: Initialize local storage with media root
        pass


class CloudStorageService(StorageService):
    """
    Cloud storage implementation (AWS S3, GCS, etc.).
    """

    def __init__(self):
        # TODO: Initialize cloud storage client
        pass
