from abc import ABC, abstractmethod
from typing import Any, Dict

class IMessageTask(ABC):
    """Contract for Celery Chat Message RAG Inference Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, conversation_id: str, content: str, provider_name: str, model_name: str | None = None) -> Dict[str, Any]:
        """
        Executes async RAG inference.
        Must return a JSON-serializable dictionary (Serialized MessageResponse).
        """
        pass