"""
Interface for Upload Job module.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import numpy as np

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse
from backend.apps.core.interfaces.dataclass.tasks.i_embed_and_save_response import IEmbedResponse, IGraphRagUploadResponse, IUploadResponse
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from neo4j_graphrag.retrievers import VectorCypherRetriever

class IUploadJob(ABC):
    """
    Contract for Document Upload Processing.
    """

    @abstractmethod
    def step_extract_and_normalize(
        self, file_path: Path, provider: EProviderName, file_caller: str = ""
    ) -> IExtractResponse:
        """
        extract and normalize text from file
        Args:
            file_path: real path of file to extract
            provider: provider name to use when extract (for example: google drive file may need google provider to extract)
            file_caller: function name of caller for logging
        Returns:
            extracted and normalized text from file
        """
        pass

    @abstractmethod
    def step_extract(
        self, file_path: Path, provider: EProviderName, file_caller: str = ""
    ) -> IExtractResponse:
        """
        extract text from file
        Args:
            file_path: real path of file or list of files to extract
            provider: provider name to use when extract (for example: google drive file may need google provider to extract)
            file_caller: function name of caller for logging
        Returns:
            extracted text from file or list of files
        """
        pass


    @abstractmethod
    def step_normalize(self, raw_text: str, file_caller: str = "") -> str:
        """
        normalize extracted text
        Args:
            raw_text: raw text to normalize
            file_caller: function name of caller for logging
        Returns:
            normalized text
        """
        pass

    @abstractmethod
    def step_chunk_and_cache(
        self, document_id: str, normalized_text: str, file_caller: str = ""
    ) -> IChunkAndCacheResponse:
        """
        chunk text and cache it
        Args:
            document_id: ID of the document
            normalized_text: normalized text to chunk and cache
            file_caller: function name of caller for logging
        Returns:
            response containing chunked and cached data
        """
        pass

    @abstractmethod
    def step_embed(
        self,
        chunk_and_cache_response: IChunkAndCacheResponse,
        provider: EProviderName,
        file_caller: str = "",
    ) -> IEmbedResponse:
        """
        embed chunked data and save to vector store
        Args:
            chunk_and_cache_response: response containing chunked and cached data
            provider: provider name to use for embedding (for example: different embedding model may be used for different provider)
            file_caller: function name of caller for logging
        Returns:
            response containing embedded data
        """
        pass

    def step_save(
        self,
        provider: EProviderName,
        document_ids: List[str],
        embedding_batches: List[np.ndarray],
        chunk_texts: List[str] = [],
        ids: np.ndarray = np.ndarray([], dtype=np.int64),
        file_caller: str = "",
    ) -> IUploadResponse | None:
        """
        save embedded data to vector store
        Args:
            provider: provider name to use for saving (for example: different vector store may be used for different provider)
            document_ids: list of document IDs corresponding to the embedded data
            embed_responses: list of embedded vectors to save
            chunk_texts: list of original chunk texts (optional, used for metadata)
            ids: list of IDs corresponding to the embedded vectors (optional, used for upsert operations)
            file_caller: function name of caller for logging
        Returns:
            response containing save results and metadata, or None if saving is not applicable for the provider
        """
        pass


    @abstractmethod
    async def step_build_knowledge_graph(
        self,
        document_id: str,
        extracted_texts: List[str],
        model_name: str,
        embedding_model_name: str,
        provider: EProviderName = EProviderName.GEMINI,
        similarity_fn: ESimilarityFn = ESimilarityFn.COSINE,
        file_caller: str = "",
    ) -> IGraphRagUploadResponse:
        """
        build knowledge graph for document
        Args:
            document_id: ID of the document
            extracted_texts: texts extracted from the document
            provider: provider name to use for building knowledge graph (for example: different LLM provider may be used for different provider)
            model_name: model name to use for building knowledge graph
            similarity_fn: function to use for calculating similarity
            file_caller: function name of caller for logging
        Returns:
            VectorCypherRetriever: the created graph retriever
        Raises:
            ValueError: If provider is invalid or document is not found
            Exception: For any other processing errors
        """
        pass
