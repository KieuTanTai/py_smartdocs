"""
Interface for Upload Job module.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse
from backend.apps.core.interfaces.dataclass.tasks.i_embed_and_save_response import IEmbedResponse, ISaveResponse

class IUploadJob(ABC):
    """
    Contract for Document Upload Processing.
    """
    
    @abstractmethod
    def step_extract(self, file_paths: List[Path], provider: EProviderName, file_caller: str = "") -> str:
        """
            extract text from file
            Args:
                file_paths: list of real paths of files to extract
                provider: provider name to use when extract (for example: google drive file may need google provider to extract)
                file_caller: function name of caller for logging
            Returns:
                extracted text from file
        """
        pass

    @abstractmethod
    def step_normalize(self, raw_text: List[str], file_caller: str = "") -> str:
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
    def step_chunk_and_cache(self, document_id: str, normalized_text: List[str], file_caller: str = "") -> IChunkAndCacheResponse:
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
    def step_embed(self, chunk_and_cache_response: IChunkAndCacheResponse, provider: EProviderName, file_caller: str = "") -> IEmbedResponse:
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


    @abstractmethod
    def step_build_knowledge_graph(self, document_id: str, extracted_texts: List[str], provider: EProviderName, model_name: str, file_caller: str = "") -> None:
        """
            build knowledge graph for document
            Args:
                document_id: ID of the document
                extracted_texts: texts extracted from the document
                provider: provider name to use for building knowledge graph
                model_name: model name to use for building knowledge graph
                file_caller: function name of caller for logging
        """
        pass