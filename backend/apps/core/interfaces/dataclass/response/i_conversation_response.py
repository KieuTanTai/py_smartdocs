from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import uuid

import faiss

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBLoadResponse
from backend.apps.services.chat.models import ConversationCacheModel, ConversationFilesModel, ConversationModel, DocumentModel, MessageModel

@dataclass
class IConversationInfoResponse:
    conversation_name: str
    conversation_title: str
    provider: EProviderName
    model_name: str
    document_urls: list[str]
    document_paths: list[Path]
    type: str = "normal" or "graph"
    create_at: Any = None 

@dataclass
class ITimeCounterResponse:
    extract_time: float
    chunk_time: float
    embedding_time: float
    save_time: float
    total_time: float
    query_time: float = 0.0 # OPTIONAL, this will be used when the conversation is used to chat, and the time_counter will be updated with the query_time, this is for future implementation of time_counter in chat application

@dataclass
class IConversationPostResponse:
    index: faiss.IndexFlatL2 | faiss.IndexIDMap
    info: IConversationInfoResponse
    time_counter: ITimeCounterResponse | None = None

@dataclass
class IConversationGetResponse:
    index: faiss.IndexFlatL2 | faiss.IndexIDMap
    info: IConversationInfoResponse

@dataclass
class IconversationDocumentGetResponse:
    document_url: Path
    files: list[ConversationFilesModel]
    db_load: Optional[IVectorDBLoadResponse] = field(default=None)

@dataclass 
class IConversationRelationshipResponse:
    conversation: ConversationModel
    cache: ConversationCacheModel
    faiss_document: DocumentModel
    conversation_files: list[ConversationFilesModel]
    messages: list[MessageModel] = field(default_factory=list)

@dataclass
class IConversationLoadResponse:
    conversation: ConversationModel
    cache: ICacheParam
    faiss_response: IVectorDBLoadResponse
    conversation_files: list[ConversationFilesModel]
    messages: list[MessageModel] = field(default_factory=list)

@dataclass
class IRetrievalTimeCounterResponse:
    retrieval_time: float
    query_time: float
    total_time: float

@dataclass
class IGraphTimeCounterResponse:
    extract_time: float
    chunk_time: float
    graph_retriever_time: float
    total_time: float
    query_time: float = 0.0 # OPTIONAL, this will be used when the conversation is used to chat, and the time_counter will be updated with the query_time, this is for future implementation of time_counter in chat application
