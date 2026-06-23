"""
Conversation tasks module.
Handles conversation bootstrapping via background workers.
"""

from dataclasses import asdict
from pathlib import Path
import uuid
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationLoadResponse, IConversationRelationshipResponse, IConversationPostResponse, IconversationDocumentGetResponse
from backend.apps.core.interfaces.services.cache.i_memory_pool import IMemoryPool
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.system.i_time_counter import ITimeCounter
from backend.apps.exceptions.exceptions import DocumentsNotReadyError
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.interfaces.tasks.i_conversation_task import IConversationTask
from backend.apps.services.chat.models import ConversationModel

class ConversationTask(IConversationTask):
    def __init__(self, conversation_job: IConversationJob, memory_pool: IMemoryPool, logger: ILogger,time_counter: ITimeCounter):
        self.conversation_job = conversation_job
        self.memory_pool = memory_pool
        self.logger = logger
        self.time_counter = time_counter

    # --- MAIN ENTRY POINT ---
    def get_all_conversations(self, user_id: str = "", file_caller: str = "") -> list[ConversationModel]:
        self.logger.info(
            f"Fetching all conversations for user_id: {user_id}",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.get_all_conversations.__name__,
        )
        return self.conversation_job.get_all_conversations(user_id, file_caller=file_caller)

    def rename(self, conversation_id: str, new_title: str, file_caller: str = "") -> ConversationModel:
        self.logger.info(
            f"Renaming conversation {conversation_id} to new title: {new_title}",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.rename.__name__,
        )
        return self.conversation_job.change_title_document(conversation_id, new_title, file_caller=file_caller)

    #! NOTE: Will continue fixing this after fix delete_job, tasks
    def remove(self, conversation_id: str, file_caller: str = "") -> int:
        self.logger.info(
            f"Removing conversation {conversation_id} and associated resources",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.remove.__name__,
        )
        # Clean up any resources associated with the conversation (e.g., cached data in FaissMemoryPool)
        return self.conversation_job.remove_conversation(conversation_id, file_caller=file_caller)

    def create_init_conversation(self, conversation_title: str = "Initial Conversation", file_caller: str = "") -> ConversationModel:
        self.logger.info(
            f"Creating initial conversation with title: {conversation_title}",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.create_init_conversation.__name__,
        )
        return self.conversation_job.create_init_conversation(conversation_title=conversation_title, file_caller=file_caller)

    def __load_conversation(
        self, conversation: ConversationModel, file_caller: str = ""
    ) -> IConversationLoadResponse:
        """
        Loads the conversation details along with the attached documents for a given conversation ID.
        This method is REQUIREMENT for frontend when switching conversation, or restart server, because it 
        will fetch the conversation, conversation files, caching files (must be existed if not deleted by remove_conversation) 
        and return to frontend to display.
        This method will clear cache, clear index of vector database, and re-cache the documents
        if the conversation is loaded again when restart server or switching conversations.
        Args:
            conversation (ConversationModel): The conversation to load.
            file_caller (str): The file caller for the conversation.
        Returns:
            IConversationLoadResponse: The response containing the conversation details, attached documents, and any relevant metadata.
        Raises:
            ValueError: If the conversation with the given ID does not exist or if there is an error loading the conversation details.
        """
        conversation_id = conversation.conversations_id
        try:
            self.logger.info(
                f"Loading conversation {conversation_id} and associated resources",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.__load_conversation.__name__,
            )
            result = self.conversation_job.check_conversation_is_valid(conversation, file_caller=file_caller)
            if not result:
                raise ValueError(f"Conversation with ID {conversation_id} not found.")

            # Load Cache
            cache = self.conversation_job.load_cache(result.conversation, file_caller=file_caller)
            if not cache:
                raise ValueError(f"Cache for conversation {conversation_id} could not be loaded.")

            # Load FAISS index for the conversation
            faiss_response = self.conversation_job.load_faiss_index(result.conversation, file_caller=file_caller)
            if not faiss_response or not faiss_response.index:
                raise ValueError(f"FAISS index for conversation {conversation_id} could not be loaded.")

            load_messages = self.conversation_job.load_messages(result.conversation, file_caller=file_caller)

            return IConversationLoadResponse(
                conversation=result.conversation,
                cache=cache,
                faiss_response=faiss_response,
                conversation_files=result.conversation_files,
                messages=load_messages
            )
        except Exception as e:
            self.logger.error(
                f"Error loading conversation {conversation_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.__load_conversation.__name__,
            )
            raise ValueError(f"Failed to load conversation {conversation_id}")

    def run(
        self,
        provider_name: EProviderName,
        model_name: str,
        conversation_id: uuid.UUID | None = None,
        summarize: str = "",
        file_caller: str = "",
    ) -> IConversationJobResponse | IConversationLoadResponse:
        if conversation_id is not None:
            conversation = self.conversation_job.check_existed_conversation(conversation_id, file_caller=file_caller)
            if conversation is not None:
                return self.__load_conversation(conversation, file_caller=file_caller)
            
        init_conversation = self.conversation_job.create_init_conversation(file_caller=file_caller)
        self.logger.info(
            f"Starting ConversationTask for conversation_id: {init_conversation.conversations_id} with provider: {provider_name} and model: {model_name}",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.run.__name__,
        )

        self.time_counter.reset()
        self.time_counter.start()

        # Validate
        self.__verify_documents_readiness(init_conversation.conversations_id)

        # Execute message generation logic
        result_dataclass = self.conversation_job.generate_bootstrap_message(init_conversation, provider_name, model_name, summarize, file_caller)
        self.time_counter.stop()
        self.logger.info(
            f"Completed ConversationTask for conversation_id: {init_conversation.conversations_id}.\n Result: {asdict(result_dataclass)}",
            source=__file__,
            call_by=file_caller,
            method_call=self.run.__name__,
        )

        elapsed = self.time_counter.get_elapsed_time()
        self.logger.info(f"ConversationTask completed in {elapsed} seconds for conversation {init_conversation.conversations_id}")
        return result_dataclass

    # --- SINGLE RESPONSIBILITY METHODS ---
    def __verify_documents_readiness(self, conversation_id: uuid.UUID) -> None:
        """Check if the documents are ready for conversation using."""
        is_ready = self.conversation_job.check_documents_ready(conversation_id)
        if not is_ready:
            self.logger.error(
                f"Documents attached to conversation {conversation_id} are not completely indexed.",
                source=Path(__file__).name,
                call_by=Path(__file__).name,
                method_call=self.__verify_documents_readiness.__name__,
            )
            raise DocumentsNotReadyError(
                f"Documents attached to conversation {conversation_id} are not completely indexed."
            )
