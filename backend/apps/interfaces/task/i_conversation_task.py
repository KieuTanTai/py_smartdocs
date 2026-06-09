from abc import ABC, abstractmethod
from typing import Any, Dict

class IConversationTask(ABC):
    """Contract for Celery Conversation Preparation Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, conversation_id: str, provider_name: str, model_name: str | None = None) -> Dict[str, Any]:
        """
        Executes conversation bootstrap flow.
        Must return a JSON-serializable dictionary (Serialized BootstrapMessageResponse).
        """
        pass