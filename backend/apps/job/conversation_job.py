from pathlib import Path
from typing import Any, cast
import uuid

# Import Interfaces
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.services.cache.i_memory_pool import IMemoryPool
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import IConversationDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_file_database import IConversationFileDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_message_database import IMessageDatabase
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, DocumentModel, MessageModel
from backend.apps.utils.get_instance_model_database import get_instance_model_database

class ConversationJob(IConversationJob):

    def __init__(self, llm_provider_factory: ILLMProviderFactory, 
                 llm_prompt_structure: ILLMPromptStructure, config_provider: IConfigProvider, 
                 database_provider: IDatabaseProvider,
                 logger: ILogger, hybrid_search_service: IHybridSearchService | None = None):
        self.llm_provider_factory = llm_provider_factory
        self.llm_prompt_structure = llm_prompt_structure
        self.config_provider = config_provider
        self.database_provider = database_provider
        self.logger = logger
        self.hybrid_search_service = hybrid_search_service
        self.document_database: IDocumentDatabase = cast(IDocumentDatabase, self.database_provider.get_model_service(DocumentModel))
        self.conversation_files_database: IConversationFileDatabase = cast(IConversationFileDatabase, self.database_provider.get_model_service(ConversationFilesModel))
        self.message_database: IMessageDatabase = cast(IMessageDatabase, self.database_provider.get_model_service(MessageModel))
        self.conversation_database: IConversationDatabase = cast(IConversationDatabase, self.database_provider.get_model_service(ConversationModel))

    def check_documents_ready(self, conversation_key:uuid.UUID, file_caller: str = "") -> bool:
        try:
            existed = self.document_database.get_by_id(conversation_key)
            self.logger.info(
                f"Checked document readiness for conversation {conversation_key}: {'Ready' if existed and existed.documents_status.lower().strip() == 'indexed' else 'Not Ready'}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_documents_ready.__name__,
            )
            if not existed or not existed.documents_status.lower().strip() == "indexed":
                return False
            return True
        except Exception as e:
            self.logger.error(
                f"Error checking document readiness for conversation {conversation_key}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_documents_ready.__name__,
            )
            return False

    def create_init_conversation(self, conversation_title: str = "Initial Conversation", file_caller: str = "") -> ConversationModel:
        try:
            conversation = self.conversation_database.create_conversation(conversation_title=conversation_title)
            self.logger.info(
                f"Created initial conversation with ID {conversation.conversations_id}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.create_init_conversation.__name__,
            )
            return conversation

        except Exception as e:
            self.logger.error(
                f"Error creating initial conversation: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.create_init_conversation.__name__,
            )
            raise ValueError("Failed to create initial conversation")

    def generate_bootstrap_message(self, conversation: ConversationModel, provider: EProviderName, model_name: str, summarize: str = "", file_caller: str = "") -> IConversationJobResponse:
        files = self.__get_conversation_files(conversation)
        if not files:
            self.logger.warning(
                f"No files found for conversation {conversation.conversations_id} when generating bootstrap message.",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.generate_bootstrap_message.__name__,
            )
            raise FileNotFoundError(f"No files found for conversation {conversation.conversations_id } when generating bootstrap message.")
        assistant_response = None
        if summarize.strip() == "":
            summarize = self.llm_prompt_structure.build_init_processed_prompt("say hi to user")
            assistant_response = self.__generate_assistant_response(summarize, provider, model_name)
        self.logger.info(
            f"Generated bootstrap message for conversation {conversation.conversations_id} with provider {provider} and model {model_name}.\n now save the message to database.",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.generate_bootstrap_message.__name__,
        )
        return IConversationJobResponse(
            conversation_id=str(conversation.conversations_id),
            status=True,
            message_model=self.__save_message(conversation, False, assistant_response.content if assistant_response else summarize),
            generate_response=assistant_response
        )
    
    def remove_conversation(self, conversation_id: str, file_caller: str = "") -> int:
        try:
            removed_count = self.conversation_database.delete(conversation_id)
            self.logger.info(
                f"Removed conversation {conversation_id}. Removed records count: {removed_count}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.remove_conversation.__name__,
            )
            return removed_count
        except Exception as e:
            self.logger.error(
                f"Error removing conversation {conversation_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.remove_conversation.__name__,
            )
        return 0

    def change_title_document(self, conversation_id: str, new_title: str, file_caller: str = "") -> ConversationModel:
        try:
            updated_count = self.conversation_database.update_title(conversation_id, new_title)
            self.logger.info(
                f"Renamed conversation {conversation_id} to '{new_title}'. Updated records count: {updated_count}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.change_title_document.__name__,
            )
            return updated_count
        except Exception as e:
            self.logger.error(
                f"Error renaming conversation {conversation_id} to '{new_title}': {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.change_title_document.__name__,
            )
            raise ValueError(f"Failed to rename conversation {conversation_id} to '{new_title}'")

    def __generate_assistant_response(self, prompt: str, provider: EProviderName, model_name: str) -> IGenerateResponse:
        llm_client = self.llm_provider_factory.get_provider(provider)
        return llm_client.generate(ICompletionRequest(provider=provider, model=model_name, prompt=prompt, context_hits=[]))

    def __save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        response = self.message_database.create_message(conversation, content, is_user_send)
        return response

    def __get_conversation_files(
        self, conversation: ConversationModel
    ) -> list[ConversationFilesModel]:
        try:
            files = self.conversation_files_database.get_by_conversation(conversation)
            self.logger.info(
                f"Retrieved {len(files)} conversation files for conversation {conversation.conversations_id}",
                source=Path(__file__).name,
                call_by=Path(__file__).name,
                method_call=self.__get_conversation_files.__name__,
            )
            return [file for file in files if file.conversation_files_id is not None]
        except Exception as e:
            self.logger.error(
                f"Error retrieving documents for conversation {conversation.conversations_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=Path(__file__).name,
                method_call=self.__get_conversation_files.__name__,
            )
            return []
