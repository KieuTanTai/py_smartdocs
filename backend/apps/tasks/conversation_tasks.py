"""
Conversation tasks module.
Handles conversation bootstrapping via background workers.
"""

from dataclasses import asdict
from typing import Any, Dict
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.interfaces.task.i_conversation_task import IConversationTask
from backend.apps.job.conversation_job import ConversationJob

class ConversationTask(Task, IConversationTask):

    # --- SINGLE RESPONSIBILITY METHODS ---

    def _get_container(self) -> BackendContainer:
        return BackendContainer()

    def _resolve_provider(self, provider_name: str) -> EProviderName:
        try:
            return EProviderName(provider_name)
        except ValueError as exc:
            raise ValueError(f"Unsupported provider: {provider_name}") from exc

    def _verify_documents_readiness(self, conversation_job: IConversationJob, conversation_id: str) -> None:
        """Kiểm tra điều kiện bắt buộc: Document phải sẵn sàng."""
        is_ready = conversation_job.check_documents_ready(conversation_id)
        if not is_ready:
            raise ConversationJob.DocumentsNotReadyError(
                f"Documents attached to conversation {conversation_id} are not completely indexed."
            )

    # --- MAIN ENTRY POINT ---

    def run(self, conversation_id: str, provider_name: str, model_name: str | None = None) -> Dict[str, Any]:
        container = self._get_container()
        provider = self._resolve_provider(provider_name)
        conversation_job: IConversationJob = container.conversation_job()

        # Validate
        self._verify_documents_readiness(conversation_job, conversation_id)

        # Thực thi logic sinh message
        result_dataclass = conversation_job.generate_bootstrap_message(
            conversation_id=conversation_id,
            provider=provider,
            model_name=model_name
        )
        
        return asdict(result_dataclass)
