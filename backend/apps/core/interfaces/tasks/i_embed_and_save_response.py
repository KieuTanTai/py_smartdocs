from dataclasses import dataclass
from typing import List

from backend.apps.core.interfaces.response.i_vector_db_response import IVectorDBUpsertResponse


@dataclass
class IEmbedAndSaveResponse:
    document_id: str
    file_key: str
    vector_ids: List[int]
    faiss_upsert: IVectorDBUpsertResponse
    bm25_upsert: IVectorDBUpsertResponse
