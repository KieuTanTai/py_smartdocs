"""
Base interfaces module.
Central import hub for all service interfaces following Inversion of Control pattern.

This module provides convenient imports for all interface definitions used across the application.
Each interface defines a contract that implementations must follow, enabling loose coupling
and flexible backend switching.
"""

# Core extraction and embedding interfaces
from backend.apps.interfaces.base_rag.extract.extractor_interface import ExtractorInterface
from backend.apps.interfaces.base_rag.embed.embedder_interface import EmbedderInterface
from backend.apps.interfaces.base_rag.locate.vector_store_interface import VectorStoreInterface

# LLM provider interfaces
from backend.apps.interfaces.llm.llm_client_interface import LLMClientInterface
from backend.apps.interfaces.llm.llm_provider_factory_interface import (
    LLMProviderFactoryInterface,
)
from backend.apps.interfaces.conversation.completion_interface import (
    CompletionRequestInterface,
    CompletionResponseInterface,
)

# Pipeline service interfaces
from backend.apps.interfaces.base_rag.extract.normalization_interface import (
    NormalizationInterface,
)
from backend.apps.interfaces.base_rag.chunk.chunking_interface import ChunkingInterface
from backend.apps.interfaces.base_rag.indexing_interface import IndexingInterface
from backend.apps.interfaces.base_rag.extract.extract_content_interface import (
    ExtractContentInterface,
)
from backend.apps.interfaces.conversation.search_interface import SearchServiceInterface
from backend.apps.interfaces.conversation.summarization_interface import (
    SummarizationServiceInterface,
)
from backend.apps.interfaces.base_rag.locate.locate_interface import LocateServiceInterface

# Application service interfaces
from backend.apps.interfaces.conversation.conversation_interface import ConversationServiceInterface
from backend.apps.interfaces.conversation.message_interface import MessageServiceInterface
from backend.apps.interfaces.document.document_storage_interface import DocumentStorageInterface

# Graph and background job interfaces
from backend.apps.interfaces.graph_rag.graph_interface import GraphServiceInterface
from backend.apps.interfaces.job.job_management_interface import JobManagementInterface

__all__ = [
    # Core interfaces
    "ExtractorInterface",
    "EmbedderInterface",
    "VectorStoreInterface",
    # LLM interfaces
    "LLMClientInterface",
    "LLMProviderFactoryInterface",
    "CompletionRequestInterface",
    "CompletionResponseInterface",
    # Pipeline interfaces
    "NormalizationInterface",
    "ChunkingInterface",
    "IndexingInterface",
    "ExtractContentInterface",
    "SearchServiceInterface",
    "SummarizationServiceInterface",
    "LocateServiceInterface",
    # Application interfaces
    "ConversationServiceInterface",
    "MessageServiceInterface",
    "DocumentStorageInterface",
    # Graph and job interfaces
    "GraphServiceInterface",
    "JobManagementInterface",
]
