from abc import ABC, abstractmethod

from celery import Task

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IconversationDocumentGetResponse
from backend.apps.services.chat.models import ConversationModel

class IConversationTask(ABC, Task):
    """Contract for Celery Conversation Preparation Task."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, conversation: ConversationModel, provider_name: EProviderName, model_name: str, summarize: str = "", file_caller: str = "") -> IConversationJobResponse:
        """
        Executes conversation bootstrap flow.
        Must return a JSON-serializable dictionary (Serialized BootstrapMessageResponse).
        Args:
            conversation (ConversationModel): The conversation for which to generate the bootstrap message.
            provider_name (EProviderName): The LLM provider to use for generating the bootstrap message.
            model_name (str): The specific model name to use for generation.
            summarize (str): A summary of the conversation, if applicable. (Optional, if you already have a summary of the conversation that you want to use during the bootstrap message generation, you can pass it here. Otherwise, you can leave it empty and the implementation can decide how to handle it.)
            file_caller (str): The file that called this method, for logging purposes.
        Returns:
            IConversationJobResponse: The response containing the generated bootstrap message and related metadata.
        """
        pass

    @abstractmethod
    def create_init_conversation(self, conversation_title: str = "Initial Conversation", file_caller: str = "") -> ConversationModel:
        """
        Creates an initial conversation with the given title.
        Args:
            conversation_title (str): The title for the new conversation.
            file_caller (str): The file that called this method, for logging purposes.
        Returns:
            ConversationModel: The model containing the created conversation details.
        """
        pass

    @abstractmethod
    def rename(self, conversation_id: str, new_title: str, file_caller: str = "") -> ConversationModel:
        """
        Renames the conversation with the given ID to the new title.
        Args:
            conversation_id (str): The ID of the conversation to rename.
            new_title (str): The new title for the conversation.
            file_caller (str): The file that called this method, for logging purposes.
        Returns:
            ConversationModel: The updated conversation model instance with the new title.
        Raises:
            ValueError: If the conversation with the given ID does not exist or if the renaming operation fails.
        """
        pass

    @abstractmethod
    def load_document(
        self, conversation_id: str, file_caller: str = ""
    ) -> IconversationDocumentGetResponse:
        """
        Load document for a given conversation.
        Args:
            conversation_id: Unique identifier for the conversation
            file_caller: Name of the file caller (for logging purposes)
        Returns:
            An IconversationDocumentGetResponse containing document URL, associated files, and optional vector DB load response
        Raises:
            ValueError: If conversation_id is invalid or document is not found
            Exception: For any other loading errors
        """
        pass

    @abstractmethod
    def remove(self, conversation_id: str, file_caller: str = "") -> int:
        """
        Removes any resources associated with the given conversation ID.
        This can include cleaning up cached data, temporary files, or any other resources that were created during the conversation preparation process.
        Args:
            conversation_id (str): The ID of the conversation whose resources should be removed.
            file_caller (str): The file that called this method, for logging purposes.
        Returns:
            int: The number of records removed (should be 1 if successful, 0 if no conversation with the given ID exists).
        """
        pass
