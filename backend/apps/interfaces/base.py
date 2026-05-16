"""
Base interfaces module.
Central import hub for all service interfaces following Inversion of Control pattern.

This module provides convenient imports for all interface definitions used across the application.
Each interface defines a contract that implementations must follow, enabling loose coupling
and flexible backend switching.
"""

# Core extraction and embedding interfaces
from backend.apps.interfaces.extractor_interface import ExtractorInterface
from backend.apps.interfaces.embedder_interface import EmbedderInterface
from backend.apps.interfaces.vector_store_interface import VectorStoreInterface

# LLM provider interfaces
from backend.apps.interfaces.llm_client_interface import LLMClientInterface
from backend.apps.interfaces.llm_provider_factory_interface import (
    LLMProviderFactoryInterface,
)
from backend.apps.interfaces.completion_interface import (
    CompletionRequestInterface,
    CompletionResponseInterface,
)

# Pipeline service interfaces
from backend.apps.interfaces.normalization_interface import (
    NormalizationServiceInterface,
)
from backend.apps.interfaces.chunking_interface import ChunkingServiceInterface
from backend.apps.interfaces.indexing_interface import IndexingServiceInterface
from backend.apps.interfaces.extract_content_interface import (
    ExtractContentServiceInterface,
)
from backend.apps.interfaces.search_interface import SearchServiceInterface
from backend.apps.interfaces.summarization_interface import (
    SummarizationServiceInterface,
)
from backend.apps.interfaces.locate_interface import LocateServiceInterface

# Application service interfaces
from backend.apps.interfaces.conversation_interface import ConversationServiceInterface
from backend.apps.interfaces.message_interface import MessageServiceInterface
from backend.apps.interfaces.document_storage_interface import DocumentStorageInterface

# Graph and background job interfaces
from backend.apps.interfaces.graph_interface import GraphServiceInterface
from backend.apps.interfaces.job_management_interface import JobManagementInterface

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
    "NormalizationServiceInterface",
    "ChunkingServiceInterface",
    "IndexingServiceInterface",
    "ExtractContentServiceInterface",
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
