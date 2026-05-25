"""
Base interfaces module.
Central import hub for all service interfaces following Inversion of Control pattern.

This module provides convenient imports for all interface definitions used across the application.
Each interface defines a contract that implementations must follow, enabling loose coupling
and flexible backend switching.
"""

# Core extraction and embedding interfaces
from backend.apps.interfaces.core.extract.i_extractor import IExtractor
from backend.apps.interfaces.core.embedding.i_embedder import IEmbedder
from backend.apps.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService

# LLM provider interfaces
from backend.apps.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.interfaces.services.chat.i_completion import (
    ICompletionRequest,
    ICompletionResponse,
)

# Pipeline service interfaces
from backend.apps.interfaces.core.chunk.i_chunking import IChunking
from backend.apps.interfaces.core.normalize.i_normalize import INormalize
from backend.apps.interfaces.services.rag_base.indexing.i_indexing import IIndexing
from backend.apps.interfaces.services.rag_base.extract.i_extract_content import (
    IExtractContent,
)
from backend.apps.interfaces.services.chat.i_search import ISearchService
from backend.apps.interfaces.services.chat.i_summarization import ISummarizationService
from backend.apps.interfaces.services.rag_base.locate.i_locate_service import ILocateService

# Application service interfaces
from backend.apps.interfaces.services.chat.i_conversation import IConversationService
from backend.apps.interfaces.services.chat.i_message import IMessageService
from backend.apps.interfaces.core.storage.i_storage import IFileStorage

# Graph and background job interfaces
from backend.apps.interfaces.services.graph_rag.i_graph import IGraphService
from backend.apps.interfaces.job.i_job_management import IJobManagement

__all__ = [
    # Core interfaces
    "IExtractor",
    "IEmbedder",
    "IVectorStoreService",
    # LLM interfaces
    "ILLMClient",
    "ILLMProviderFactory",
    "ICompletionRequest",
    "ICompletionResponse",
    # Pipeline interfaces
    "INormalize",
    "IChunking",
    "IIndexing",
    "IExtractContent",
    "ISearchService",
    "ISummarizationService",
    "ILocateService",
    # Application interfaces
    "IConversationService",
    "IMessageService",
    "IFileStorage",
    # Graph and job interfaces
    "IGraphService",
    "IJobManagement",
]
