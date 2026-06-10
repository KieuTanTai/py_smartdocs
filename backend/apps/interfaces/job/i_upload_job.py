"""
Interface for Upload Job module.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse
from backend.apps.core.interfaces.tasks.i_embed_and_save_response import IEmbedAndSaveResponse

class IUploadJob(ABC):
    """
    Contract for Document Upload Processing.
    """
    
    @abstractmethod
    def step_extract(self, file_path: Path, provider: EProviderName, file_caller: str = "") -> str:
        """
            extract text from file
            Args:
                file_path: real path of file to extract
                provider: provider name to use when extract (for example: google drive file may need google provider to extract)
                file_caller: function name of caller for logging
            Returns:
                extracted text from file
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
    def step_chunk_and_cache(self, document_id: str, normalized_text: str, file_caller: str = "") -> IChunkAndCacheResponse:
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
    def step_embed_and_save(self, chunk_data: IChunkAndCacheResponse, provider: EProviderName, file_caller: str = "") -> IEmbedAndSaveResponse:
        """
            embed chunked text and save it
            Args:
                chunk_data: data containing chunked and cached information
                provider: provider name to use for embedding
                file_caller: function name of caller for logging
            Returns:
                response containing embedding and saving information
        """
        pass