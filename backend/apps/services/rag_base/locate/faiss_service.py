from pathlib import Path

import numpy as np
import faiss

from backend.apps.core.interfaces.services.cache.i_singleton_cache import ISingletonCache
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import (
    IVectorStoreService,
)
from backend.apps.services.rag_base.locate.vector_store_base import VectorStoreBase
from backend.apps.core.interfaces.system.i_logging import ILogger


class FaissService(IVectorStoreService):
    """
    singleton service for FAISS vector store operations.
    This class provides methods to upsert, search, delete, cache vectors and get collection info using FAISS library.
    It is designed to be used as a vector store backend in the LocateService.
    """

    def __init__(
        self,
        metadata_dir: Path,
        singleton_cache: ISingletonCache,
        logger: ILogger,
    ):
        self.metadata_dir = metadata_dir
        self.singleton_cache = singleton_cache
        self.logger = logger

    def upsert(self, vector_id, vector, metadata):
        

    def search(self, query_vector, limit=5, filters=None):
        raise NotImplementedError("Faiss search is not implemented yet")

    def delete(self, vector_id):
        raise NotImplementedError("Faiss delete is not implemented yet")

    def get_collection_info(self):
        raise NotImplementedError("Faiss collection info is not implemented yet")

    def __is_existed_in_cache(self, index_key: str) -> bool:
        return self.singleton_cache.exists(index_key)
    
    def __is_existed_in_metadata(self, vector_id: str) -> bool:
        metadata_path = self.metadata_dir / vector_id
        return metadata_path.exists()