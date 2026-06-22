from dataclasses import dataclass, field
from pathlib import Path

from backend.apps.core.enums.e_provider_name import EProviderName


@dataclass
class IUploadApplicationRequest:
    """Request dataclass for upload application endpoint.
    Tạo conversation + chạy pipeline upload tài liệu.
    """
    provider: EProviderName
    model_name: str
    document_paths: list[Path] = field(default_factory=list)
    document_urls: list[str] = field(default_factory=list)
    type: str = "normal"  # "normal" (base RAG) hoặc "graph" (graph RAG)


@dataclass
class ISendMessageApplicationRequest:
    """Request dataclass for send message application endpoint.
    Gửi tin nhắn vào conversation, RAG retrieval + LLM generate.
    """
    conversation_id: str
    message: str
    provider: EProviderName
    model_name: str
    type: str = "normal"  # "normal" (base RAG) hoặc "graph" (graph RAG)


@dataclass
class IDeleteConversationApplicationRequest:
    """Request dataclass for delete conversation application endpoint.
    Xóa conversation + tất cả dữ liệu liên quan (messages, files, FAISS, BM25, cache, graph).
    """
    conversation_id: str
