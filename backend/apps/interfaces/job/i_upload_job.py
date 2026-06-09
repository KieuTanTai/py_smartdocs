"""
Interface for Upload Job module.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_dataclass_upload_job import ChunkAndCacheResponse, EmbedAndSaveResponse

class IUploadJob(ABC):
    """
    Contract for Document Upload Processing.
    """
    
    @abstractmethod
    def step_extract(self, file_path: Path, provider: EProviderName) -> str:
        pass

    @abstractmethod
    def step_normalize(self, raw_text: str) -> str:
        pass

    @abstractmethod
    def step_chunk_and_cache(self, document_id: str, normalized_text: str) -> ChunkAndCacheResponse:
        pass

    @abstractmethod
    def step_embed_and_save(self, chunk_data: ChunkAndCacheResponse, provider: EProviderName) -> EmbedAndSaveResponse:
        pass