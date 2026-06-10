"""
Conversation tasks module.
Handles conversation bootstrapping via background workers.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_conversation_job import IConversationJobResponse
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.exceptions.exceptions import DocumentsNotReadyError
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.interfaces.task.i_conversation_task import IConversationTask
from backend.apps.job.conversation_job import ConversationJob

class ConversationTask(Task, IConversationTask):
    def __init__(self, conversation_job: IConversationJob, logger: ILogger):
        self.conversation_job = conversation_job
        self.logger = logger

    # --- SINGLE RESPONSIBILITY METHODS ---
    def _verify_documents_readiness(self, conversation_job: IConversationJob, conversation_id: str) -> None:
        """Check if the documents are ready for processing."""
        is_ready = conversation_job.check_documents_ready(conversation_id)
        if not is_ready:
            self.logger.error(
                f"Documents attached to conversation {conversation_id} are not completely indexed.",
                source=__file__,
                call_by=Path(__file__).name,
                method_call=self._verify_documents_readiness.__name__,
            )
            raise DocumentsNotReadyError(
                f"Documents attached to conversation {conversation_id} are not completely indexed."
            )

    # --- MAIN ENTRY POINT ---

    def run(self, conversation_id: str, provider_name: EProviderName, model_name: str | None = None, file_caller: str = "") -> IConversationJobResponse:
        self.logger.info(
            f"Starting ConversationTask for conversation_id: {conversation_id} with provider: {provider_name} and model: {model_name}",
            source=__file__,
            call_by=file_caller,
            method_call=self.run.__name__,
        )
        # Validate
        self._verify_documents_readiness(self.conversation_job, conversation_id)

        # Execute message generation logic
        result_dataclass = self.conversation_job.generate_bootstrap_message(
            conversation_id=conversation_id,
            provider=provider_name,
            model_name=model_name
        )
        self.logger.info(
            f"Completed ConversationTask for conversation_id: {conversation_id}. Generated assistant message: {result_dataclass.assistant_message[:100]}",
            source=__file__,
            call_by=file_caller,
            method_call=self.run.__name__,
        )
        return result_dataclass
