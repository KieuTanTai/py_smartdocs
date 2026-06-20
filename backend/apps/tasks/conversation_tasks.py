"""
Conversation tasks module.
Handles conversation bootstrapping via background workers.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict
import uuid
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.services.cache.i_faiss_memory_pool import IFaissMemoryPool
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.system.i_time_counter import ITimeCounter
from backend.apps.exceptions.exceptions import DocumentsNotReadyError
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.interfaces.tasks.i_conversation_task import IConversationTask
from backend.apps.services.chat.models import ConversationModel

class ConversationTask(IConversationTask):
    def __init__(self, conversation_job: IConversationJob, faiss_memory_pool: IFaissMemoryPool, logger: ILogger,time_counter: ITimeCounter):
        self.conversation_job = conversation_job
        self.faiss_memory_pool = faiss_memory_pool
        self.logger = logger
        self.time_counter = time_counter

    # --- MAIN ENTRY POINT ---
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
        self.faiss_memory_pool.remove_from_pool(conversation_id)
        return self.conversation_job.remove_conversation(conversation_id, file_caller=file_caller)

    def create_init_conversation(self, conversation_title: str = "Initial Conversation", file_caller: str = "") -> ConversationModel:
        self.logger.info(
            f"Creating initial conversation with title: {conversation_title}",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.create_init_conversation.__name__,
        )
        return self.conversation_job.create_init_conversation(conversation_title=conversation_title, file_caller=file_caller)

    def run(self, conversation: ConversationModel, provider_name: EProviderName, model_name: str, summarize: str = "", file_caller: str = "") -> IConversationJobResponse:
        self.logger.info(
            f"Starting ConversationTask for conversation_id: {conversation.conversations_id} with provider: {provider_name} and model: {model_name}",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.run.__name__,
        )

        self.time_counter.reset()
        self.time_counter.start()

        # Validate
        self.__verify_documents_readiness(conversation.conversations_id)

        # Execute message generation logic
        result_dataclass = self.conversation_job.generate_bootstrap_message(conversation, provider_name, model_name, summarize, file_caller)
        self.time_counter.stop()
        self.logger.info(
            f"Completed ConversationTask for conversation_id: {conversation.conversations_id}.\n Result: {asdict(result_dataclass)}",
            source=__file__,
            call_by=file_caller,
            method_call=self.run.__name__,
        )

        elapsed = self.time_counter.get_elapsed_time()
        self.logger.info(f"ConversationTask completed in {elapsed} seconds for conversation {conversation.conversations_id}")
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
