from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List
import uuid
import faiss
import numpy as np
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import IEmbeddingResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IGraphTimeCounterResponse, ITimeCounterResponse
from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBUpsertResponse
from neo4j_graphrag.retrievers import VectorCypherRetriever

from backend.apps.services.chat.models import ConversationFilesModel

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
    faiss_file_id: uuid.UUID
    vector_ids: list[int]
    embeddings_stack: np.ndarray
    documents: list[IDocumentResponse]
    faiss_upsert: IVectorDBUpsertResponse
    bm25_upsert: IVectorDBUpsertResponse | None = None
    time_counter: ITimeCounterResponse | None = None
    conversation_files: list[ConversationFilesModel] = field(default_factory=list)
    summarize: IGenerateResponse | None = None
    created_at: Any = None

@dataclass
class IDocumentResponse:
    document_id: str
    path: Path

@dataclass 
class IGraphRagParam:
    conversation_id: uuid.UUID
    document_id: str
    chunk_content: str
    chunk_id: np.int64

@dataclass
class IGraphRagUploadResponse:
    conversation_id: uuid.UUID
    list_document_ids: list[str]
    graph_param_list: list[IGraphRagParam]
    graph_retriever: VectorCypherRetriever
    created_at: Any = None
    conversation_name: str = ""
    conversation_files: list[ConversationFilesModel] = field(default_factory=list)
    time_counter: IGraphTimeCounterResponse | None = None
