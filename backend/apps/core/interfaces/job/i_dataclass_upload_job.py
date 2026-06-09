from dataclasses import dataclass
from typing import List


@dataclass
class VectorStoreUpsertStatus:
    uuid: str
    is_success: bool

@dataclass
class ChunkAndCacheResponse:
    document_id: str
    cache_key: str
    chunk_keys: List[str]
    chunk_texts: List[str]

@dataclass
class EmbedAndSaveResponse:
    document_id: str
    file_key: str
    vector_ids: List[int]
    faiss_upsert: VectorStoreUpsertStatus
    bm25_upsert: VectorStoreUpsertStatus