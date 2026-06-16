from dataclasses import dataclass
from typing import List
import faiss
import numpy as np
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import IEmbeddingResponse
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBUpsertResponse

@dataclass
class IEmbedResponse:
    document_id: str
    embeded_metadata: List[IEmbeddingResponse]

@dataclass
class ISaveResponse:
    faiss_index: faiss.IndexFlatL2 | faiss.IndexIDMap
    faiss_file_name: str
    vector_ids: List[int]
    faiss_upsert: IVectorDBUpsertResponse
    bm25_upsert: IVectorDBUpsertResponse | None = None
