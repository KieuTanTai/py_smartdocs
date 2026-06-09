from dataclasses import asdict
from typing import Any, Dict
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.interfaces.job.i_message_job import IMessageJob
from backend.apps.interfaces.task.i_message_task import IMessageTask

class MessageTask(Task, IMessageTask):

    def run(self, conversation_id: str, content: str, provider_name: str, model_name: str | None = None) -> Dict[str, Any]:
        container = BackendContainer()
        try:
            provider = EProviderName(provider_name)
        except ValueError as exc:
            raise ValueError(f"Unsupported provider: {provider_name}") from exc

        message_job: IMessageJob = container.message_job()

        result_dataclass = message_job.run(
            conversation_id=conversation_id,
            content=content,
            provider=provider,
            model_name=model_name
        )
        
        return asdict(result_dataclass)