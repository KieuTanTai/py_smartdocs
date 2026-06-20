from abc import ABC, abstractmethod

from celery import Task

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.job.i_conversation_job import IConversationJobResponse

class IConversationTask(ABC, Task):
    """Contract for Celery Conversation Preparation Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, conversation_id: str, provider_name: EProviderName, model_name: str, file_caller: str = "") -> IConversationJobResponse:
        """
        Executes conversation bootstrap flow.
        Must return a JSON-serializable dictionary (Serialized BootstrapMessageResponse).
        Args:
            conversation_id (str): The ID of the conversation to prepare.
            provider_name (EProviderName): The LLM provider to use for generating the bootstrap message.
            model_name (str): The specific model name to use for generation.
            file_caller (str): The file that called this method, for logging purposes.
        Returns:
            IConversationJobResponse: The response containing the generated bootstrap message and related metadata.
        """
        pass
    
    @abstractmethod
    def remove(self, conversation_id: str) -> None:
        """
        Removes any resources associated with the given conversation ID.
        This can include cleaning up cached data, temporary files, or any other resources that were created during the conversation preparation process.
        Args:
            conversation_id (str): The ID of the conversation whose resources should be removed.
        """
        pass