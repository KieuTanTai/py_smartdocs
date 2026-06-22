from abc import ABC, abstractmethod
from dataclasses import dataclass
import uuid
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IconversationDocumentGetResponse
from backend.apps.services.chat.models import ConversationModel

class IConversationJob(ABC):
    """Contract for Conversation Preparation Processing."""
    
    @abstractmethod
    def check_documents_ready(self, conversation_key: uuid.UUID, file_caller: str = "") -> bool:
        """Checks if all documents attached to the conversation are ready (e.g., indexed) for processing.
        Args:
            conversation_key (uuid.UUID): The key of the conversation to check.
            file_caller (str): The file caller for the conversation.
        Returns:
            bool: True if all documents are ready, False otherwise.
        """
        pass

    @abstractmethod
    def change_title_document(self, conversation_id: str, new_title: str, file_caller: str = "") -> ConversationModel:
        """Changes the title of the conversation document.
        Args:
            conversation_id (str): The ID of the conversation to rename.
            new_title (str): The new title for the conversation.
            file_caller (str): The file caller for the conversation.
        Returns:
            ConversationModel: The updated conversation model instance with the new title.
        """
        pass

    @abstractmethod
    def remove_conversation(self, conversation_id: str, file_caller: str = "") -> int:
        """Removes the conversation and any associated resources.
        Args:
            conversation_id (str): The ID of the conversation to remove.
            file_caller (str): The file caller for the conversation.
        Returns:
            int: The number of records removed (should be 1 if successful, 0 if no conversation with the given ID exists).
        """
        pass

    @abstractmethod
    def create_init_conversation(self, conversation_title: str = "Initial Conversation", file_caller: str = "") -> ConversationModel:
        """Creates an initial conversation entry in the database.
        Args:
            conversation_title (str): The title of the conversation to create.
            file_caller (str): The file caller for the conversation.
        Returns:
            ConversationModel: The created conversation model instance.
        Raises:
            ValueError: If the conversation creation fails.
        """
        pass

    @abstractmethod
    def generate_bootstrap_message(self, conversation: ConversationModel, provider: EProviderName, model_name: str, summarize: str = "", file_caller: str = "") -> IConversationJobResponse:
        """
        Need create an initial conversation first before calling this method to ensure that the conversation entry exists in the database 
        and can be associated with the generated bootstrap message.
        Generates the initial assistant message for a conversation based on the attached documents and the specified LLM provider/model.
        Recommended to be called after ensuring that all documents are ready using the check_documents_ready method and have been indexed properly.
        Args:
            conversation (ConversationModel): The conversation for which to generate the bootstrap message.
            provider (EProviderName): The LLM provider to use for generating the message.
            model_name (str): The specific model name to use for generation.
            summarize (str): Optional summary of the conversation.
            file_caller (str): The file caller for the conversation.
        Returns:
            IConversationJobResponse: The response containing the generated bootstrap message and related metadata.
        """
        pass

    @abstractmethod
    def load_document(self, conversation_id: str, file_caller: str = "") -> IconversationDocumentGetResponse:
        """
        load document information for a conversation, which can be used for further processing such as building knowledge graph, or for displaying the document information in the UI, etc. The document information is stored in the database with the conversation_id as reference, and it includes the document ids and paths, etc.
        Args:
            conversation_id: the ID of the conversation to load documents for
            file_caller: function name of caller for logging
        Returns:
            IconversationDocumentGetResponse containing the document information for the conversation
        Raises:
            ValueError: If conversation is not found or has no associated documents
            Exception: For any other processing errors
        """
        pass