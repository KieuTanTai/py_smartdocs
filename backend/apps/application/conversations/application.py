from pathlib import Path
import uuid

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationLoadResponse
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.application.conversation.i_conversation_application import IConversationApplication
from backend.apps.interfaces.tasks.i_conversation_task import IConversationTask
from backend.apps.services.chat.models import ConversationModel


class ConversationApplication(IConversationApplication):
    def __init__(self, conversation_task: IConversationTask, logger: ILogger):
        self.conversation_task = conversation_task
        self.logger = logger

    def create_init_conversation(self, conversation_title: str = "<New Conversation>", file_caller: str = "") -> ConversationModel:
        self.logger.info(f"Creating initial conversation with title: {conversation_title}",
                         Path(__file__).name, file_caller, self.create_init_conversation.__name__)
        return self.conversation_task.create_init_conversation(conversation_title=conversation_title)

    def load_conversation(self, conversation_id: str, file_caller: str = "") -> ConversationModel:
        """Load an existing conversation by its ID."""
        self.logger.info(f"Loading conversation with id: {conversation_id}",
                         Path(__file__).name, file_caller, self.load_conversation.__name__)
        # Get the conversation from the task layer
        conversations = self.conversation_task.get_all_conversations(user_id="", file_caller=file_caller)
        for conv in conversations:
            if str(conv.conversations_id) == conversation_id:
                return conv
        raise ValueError(f"Conversation with id {conversation_id} not found")

    def run_application_pipeline(self, provider_name: EProviderName, 
                                                 model_name: str, conversation: ConversationModel | None = None, summarize: str = "", file_caller: str = "") -> IConversationJobResponse | IConversationLoadResponse:
        self.logger.info(f"Running application pipeline for provider: {provider_name}, model: {model_name}, conversation: {conversation.conversations_id if conversation else None}",
                         Path(__file__).name, file_caller, self.run_application_pipeline.__name__)
        response = self.conversation_task.run(provider_name=provider_name, model_name=model_name, conversation=conversation, summarize=summarize, file_caller=file_caller)
        if isinstance(response, IConversationJobResponse):
            self.logger.info(f"Application pipeline completed for conversation_id: {response.conversation_id}, provider: {provider_name}, model: {model_name}",
                             Path(__file__).name, file_caller, self.run_application_pipeline.__name__)
        elif isinstance(response, IConversationLoadResponse):
            self.logger.info(f"Loaded existing conversation for conversation_id: {response.conversation.conversations_id}, provider: {provider_name}, model: {model_name}",
                             Path(__file__).name, file_caller, self.run_application_pipeline.__name__)
        return response

    def list_conversations(self, user_id: str = "", file_caller: str = "") -> list[ConversationModel]:
        self.logger.info(f"Listing conversations for user_id: {user_id}",
                         Path(__file__).name, file_caller, self.list_conversations.__name__)
        return self.conversation_task.get_all_conversations(user_id=user_id)
    
    def rename_conversation(self, conversation_id: str, new_title: str, file_caller: str = "") -> ConversationModel:
        self.logger.info(f"Renaming conversation with id: {conversation_id} to new title: {new_title}",
                         Path(__file__).name, file_caller, self.rename_conversation.__name__)
        return self.conversation_task.rename(conversation_id=conversation_id, new_title=new_title)