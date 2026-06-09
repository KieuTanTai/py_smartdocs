from abc import ABC, abstractmethod
from typing import Any, Dict

class IUploadTask(ABC):
    """Contract for Celery Upload Processing Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Celery Task routing name"""
        pass

    @abstractmethod
    def run(self, document_id: str, provider_name: str) -> Dict[str, Any]:
        """
        Executes document RAG pipeline via UploadJob.
        Must return a JSON-serializable dictionary.
        """
        pass