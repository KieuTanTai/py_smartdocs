from dataclasses import dataclass
from typing import Any

import faiss

from backend.apps.core.enums.e_provider_name import EProviderName

@dataclass
class IConversationPostResponse:
    index: faiss.IndexFlatL2 | faiss.IndexIDMap
    info: IConversationInfoResponse
    time_counter: IConversationPostTimeCounterResponse

@dataclass
class IConversationGetResponse:
    index: faiss.IndexFlatL2 | faiss.IndexIDMap
    info: IConversationInfoResponse

@dataclass
class IConversationPostTimeCounterResponse:
    upload_time: float
    embedding_time: float
    index_time: float
    query_time: float
    response_time: float
    total_time: float

@dataclass
class IConversationInfoResponse:
    conversation_id: str
    provider: EProviderName
    model_name: str
    document_urls: list[str]
    document_paths: list[str]
    type: str = "normal" or "graph"
    create_at: Any = None