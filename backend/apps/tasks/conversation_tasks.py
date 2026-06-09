from dataclasses import asdict
from typing import Any, Dict
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.job.conversation_job import ConversationJob

from backend.apps.interfaces.task.i_conversation_task import IConversationTask
from backend.apps.interfaces.job.i_conversation_job import IConversationJob

class ConversationTask(Task, IConversationTask):
    name = "backend.apps.tasks.conversation_tasks.prepare_conversation"

    def run(self, conversation_id: str, provider_name: str, model_name: str | None = None) -> Dict[str, Any]:
        container = BackendContainer()
        try:
            provider = EProviderName(provider_name)
        except ValueError as exc:
            raise ValueError(f"Unsupported provider: {provider_name}") from exc

        conversation_job: IConversationJob = container.conversation_job()

        is_ready = conversation_job.check_documents_ready(conversation_id)
        if not is_ready:
            raise ConversationJob.DocumentsNotReadyError(
                f"Documents attached to conversation {conversation_id} are not ready"
            )

        result_dataclass = conversation_job.generate_bootstrap_message(
            conversation_id=conversation_id,
            provider=provider,
            model_name=model_name
        )
        
        return asdict(result_dataclass)