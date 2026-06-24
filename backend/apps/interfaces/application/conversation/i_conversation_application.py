from abc import ABC, abstractmethod

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationLoadResponse
from backend.apps.services.chat.models import ConversationModel

class IConversationApplication(ABC):
    @abstractmethod
    def create_init_conversation(self, conversation_title: str = "<New Conversation>", file_caller: str = "") -> ConversationModel:
        """
        Create a new conversation for a user.
        :param user_id: The ID of the user creating the conversation.
        :param conversation_title: The title of the new conversation.
        :param file_caller: Optional parameter to specify the file caller for logging purposes.
        :return: A ConversationModel instance representing the newly created conversation.
        """
        pass

    @abstractmethod
    def rename_conversation(self, conversation_id: str, new_title: str, file_caller: str = "") -> ConversationModel:
        """
        Rename an existing conversation.
        :param conversation_id: The ID of the conversation to rename.
        :param new_title: The new title for the conversation.
        :param file_caller: Optional parameter to specify the file caller for logging purposes.
        :return: A ConversationModel instance representing the renamed conversation.
        """
        pass

    # @abstractmethod
    # def remove_conversation(self, conversation_id: str, file_caller: str = "") -> int:
    #     pass

    @abstractmethod
    def list_conversations(self, user_id: str = "", file_caller: str = "") -> list:
        """
        List all conversations for a user.
        :param user_id: The ID of the user whose conversations to list.
        :param file_caller: Optional parameter to specify the file caller for logging purposes.
        :return: A list of ConversationModel instances representing the user's conversations.
        """
        pass

    @abstractmethod
    def run_application_pipeline(
        self,
        provider_name: EProviderName,
        model_name: str,
        conversation: ConversationModel | None,
        summarize: str = "",
        file_caller: str = "",
    ) -> IConversationJobResponse | IConversationLoadResponse:
        """
        Run the application pipeline for a conversation.
        :param provider_name: The name of the provider to use for the pipeline.
        :param model_name: The name of the model to use for the pipeline.
        :param conversation: The ConversationModel instance representing the conversation to process.
        :param summarize: Optional parameter to specify a summary for the conversation.
        :param file_caller: Optional parameter to specify the file caller for logging purposes.
        :return: A dictionary containing the results of the application pipeline.
        """
        pass
