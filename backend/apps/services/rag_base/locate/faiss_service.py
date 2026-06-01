from pathlib import Path

import numpy as np
import faiss

from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.services.rag_base.locate.vector_store_base import VectorStoreBase
from backend.apps.core.interfaces.system.i_logging import ILogger


class FaissService(VectorStoreBase, IVectorStoreService):
    """
        singleton service for FAISS vector store operations. 
        This class provides methods to upsert, search, delete, cache vectors and get collection info using FAISS library. 
        It is designed to be used as a vector store backend in the LocateService.
    """
    def __init__(
        self,
        metadata_dir: Path | None = None,
        logger: ILogger | None = None,
    ):
        super().__init__(
            metadata_dir=metadata_dir,
            logger=logger,
        )

    async def upsert(self, vector_id, vector, metadata):
        raise NotImplementedError("Faiss upsert is not implemented yet")

    async def search(self, query_vector, limit=5, filters=None):
        raise NotImplementedError("Faiss search is not implemented yet")

    async def delete(self, vector_id):
        raise NotImplementedError("Faiss delete is not implemented yet")

    async def get_collection_info(self):
        raise NotImplementedError("Faiss collection info is not implemented yet")
