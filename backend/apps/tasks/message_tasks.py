"""
Message tasks module.
Handles async RAG chat queries.
"""

from dataclasses import asdict
from typing import Any, Dict
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.interfaces.job.i_message_job import IMessageJob
from backend.apps.interfaces.task.i_message_task import IMessageTask

class MessageTask(Task, IMessageTask):
    name = "backend.apps.tasks.message_tasks.process_chat_message"

    # --- SINGLE RESPONSIBILITY METHODS ---

    def _get_container(self) -> BackendContainer:
        return BackendContainer()

    def _resolve_provider(self, provider_name: str) -> EProviderName:
        try:
            return EProviderName(provider_name)
        except ValueError as exc:
            raise ValueError(f"Unsupported provider: {provider_name}") from exc

    def _execute_rag_inference(self, message_job: IMessageJob, conversation_id: str, content: str, provider: EProviderName, model_name: str | None) -> Dict[str, Any]:
        """Đóng gói logic gọi RAG và convert kết quả."""
        result_dataclass = message_job.run(
            conversation_id=conversation_id,
            content=content,
            provider=provider,
            model_name=model_name
        )
        return asdict(result_dataclass)

    # --- MAIN ENTRY POINT ---

    def run(self, conversation_id: str, content: str, provider_name: str, model_name: str | None = None) -> Dict[str, Any]:
        container = self._get_container()
        provider = self._resolve_provider(provider_name)
        message_job: IMessageJob = container.message_job()

        return self._execute_rag_inference(
            message_job=message_job,
            conversation_id=conversation_id,
            content=content,
            provider=provider,
            model_name=model_name
        )