from abc import ABC, abstractmethod
from typing import Any, Dict

class IDocumentTask(ABC):
    """Contract for Celery Document Processing Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Celery Task routing name (e.g., 'tasks.process_upload')"""
        pass

    @abstractmethod
    def run(self, document_id: str, provider_name: str) -> Dict[str, Any]:
        """
        Executes document RAG pipeline.
        Must return a JSON-serializable dictionary (Serialized EmbedAndSaveResponse).
        """
        pass