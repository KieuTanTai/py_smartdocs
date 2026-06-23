from abc import ABC, abstractmethod

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
    def load_conversation(self, conversation_id: str, file_caller: str = "") -> ConversationModel:
        """
        Load an existing conversation by its ID.
        :param conversation_id: The ID of the conversation to load.
        :param file_caller: Optional parameter to specify the file caller for logging purposes.
        :return: A ConversationModel instance representing the loaded conversation.
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
