from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List
import faiss
import numpy as np
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import IEmbeddingResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IGraphTimeCounterResponse, ITimeCounterResponse
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBUpsertResponse
from neo4j_graphrag.retrievers import VectorCypherRetriever

@dataclass
class IExtractMapping:
    document_path: Path
    extract_content: IExtractResponse

@dataclass
class IEmbedResponse:
    document_id: str
    embeddings: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))

@dataclass
class IUploadResponse:
    faiss_index: faiss.IndexFlatL2 | faiss.IndexIDMap
    faiss_file_name: str
    vector_ids: List[int]
    documents: List[IDocumentResponse]
    faiss_upsert: IVectorDBUpsertResponse
    bm25_upsert: IVectorDBUpsertResponse | None = None
    time_counter: ITimeCounterResponse | None = None
    crated_at: Any = None

@dataclass
class IDocumentResponse:
    document_id: str
    path: Path
    summary: str = ""

@dataclass
class IGraphRagUploadResponse:
    conversation_name: str
    responses: List[IGraphRagUploadResponseWithTimeCounter]
    crated_at: Any = None

@dataclass
class IGraphRagUploadResponseWithTimeCounter:
    document_id: str
    graph_retriever: VectorCypherRetriever
    time_counter: IGraphTimeCounterResponse | None = None
