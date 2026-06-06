from pathlib import Path

from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import (
    IVectorStoreService,
)
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import (
    ILocateService,
)
from backend.apps.services.rag_base.locate.faiss_service import FaissService
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.interfaces.system.i_logging import ILogger


class LocateService(ILocateService):
    def __init__(
        self,
        metadata_dir: Path,
        logger: ILogger,
    ):
        self.metadata_dir = metadata_dir
        self.logger = logger

    def get_vector_store(self, backend: EBackendStorageName) -> IVectorStoreService:
        """Get vector store service instance based on backend name.
        Args:
            backend: Name of vector store backend (e.g., "faiss")
        Returns:
            IVectorStoreService instance for specified backend
        """
        if backend == EBackendStorageName.FAISS:
            faiss_service = FaissService(metadata_dir=self.metadata_dir, logger=self.logger)
            self.logger.info("Using FAISS vector store")
            self.logger.info(f"FAISS metadata directory: {self.metadata_dir}")
            return faiss_service
        self.logger.error(f"Unsupported vector store backend: {backend}")
        raise ValueError(f"Unsupported vector store backend: {backend}")
