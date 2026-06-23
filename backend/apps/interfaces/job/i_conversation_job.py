from abc import ABC, abstractmethod
from dataclasses import dataclass
import uuid
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationRelationshipResponse, IconversationDocumentGetResponse
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBLoadResponse
from backend.apps.services.chat.models import ConversationModel, MessageModel

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

    # pipeline: Load existed conversation, check if all documents are ready, generate bootstrap message, and return the response
    @abstractmethod
    def check_conversation_is_valid(self, conversation: ConversationModel, file_caller: str = "") -> IConversationRelationshipResponse | None:
        """
        Checks if the conversation with the given ID is valid and has all necessary resources (e.g., cache, document, files) associated with it.
        Args:
            conversation (ConversationModel): The conversation to check.
            file_caller (str): The file caller for the conversation.
        Returns:
            IConversationRelationshipResponse: Returns an IConversationRelationshipResponse if the conversation is valid; otherwise, returns None.
        Raises:
            ValueError: If the conversation with the given ID does not exist or if the validation check fails.
        """
        pass

    @abstractmethod
    def load_faiss_index(
        self, conversation: ConversationModel, file_caller: str = ""
    ) -> IVectorDBLoadResponse | None:
        """
        Loads the FAISS index for the given conversation from the vector store service.
        Args:
            conversation (ConversationModel): The conversation for which to load the FAISS index.
            file_caller (str): The file caller for the conversation.
        Returns:
            IVectorDBLoadResponse | None: Returns an IVectorDBLoadResponse containing the loaded FAISS index and related conversation info if successful; otherwise, returns None.
        Raises:
            ValueError: If the conversation is invalid or if the FAISS index loading fails.
        """
        pass

    @abstractmethod
    def load_messages(self, conversation: ConversationModel, file_caller: str = "") -> list[MessageModel]:
        """
        Loads all messages associated with the given conversation ID.
        Args:
            conversation (ConversationModel): The conversation for which to load messages.
            file_caller (str): The file caller for the conversation.
        Returns:
            list[MessageModel]: A list of MessageModel objects representing the messages associated with the conversation.
        Raises:
            ValueError: If the conversation with the given ID does not exist or if message loading fails.
        """
        pass

    @abstractmethod
    def load_cache(self, conversation: ConversationModel, file_caller: str = "") -> ICacheParam | None:
        """
        Loads the cache associated with the given conversation ID.
        Args:
            conversation (ConversationModel): The conversation for which to load the cache.
            file_caller (str): The file caller for the conversation.
        Returns:
            ICacheParam | None: The cache parameter associated with the conversation.
        Raises:
            ValueError: If the conversation with the given ID does not exist or if cache loading fails.
        """
        pass

    @abstractmethod
    def check_existed_conversation(
        self, conversation_id: uuid.UUID, file_caller: str = ""
    ) -> ConversationModel | None:
        """
        Checks if a conversation with the given ID exists.
        Args:
            conversation_id (uuid.UUID): The ID of the conversation for which to check existence.
            file_caller (str): The file caller for the conversation.
        Returns:
            ConversationModel | None: The conversation model if it exists, or None if not found.
        """
        pass
