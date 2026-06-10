"""
Message tasks module.
Handles async RAG chat queries.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_message_job import IMessageJobResponse
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.job.i_message_job import IMessageJob
from backend.apps.interfaces.task.i_message_task import IMessageTask

class MessageTask(Task, IMessageTask):

    def __init__(self, message_job: IMessageJob, logger: ILogger):
        self.message_job = message_job
        self.logger = logger

    # --- SINGLE RESPONSIBILITY METHODS ---
    def _execute_rag_inference(self, message_job: IMessageJob, conversation_id: str, content: str, provider: EProviderName, model_name: str | None) -> IMessageJobResponse:
        """Execute RAG inference."""
        result_dataclass = message_job.run(
            conversation_id=conversation_id,
            content=content,
            provider=provider,
            model_name=model_name
        )
        return result_dataclass

    # --- MAIN ENTRY POINT ---
    @property
    def name(self) -> str:
        """Return the task name for routing."""
        return Path(__file__).stem  # Dynamic name based on filename

    def run(self, conversation_id: str, content: str, provider_name: EProviderName, model_name: str | None = None) -> IMessageJobResponse:
        """Execute the message task."""
        self.logger.info(f"Starting MessageTask for conversation {conversation_id}", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.run.__name__)
        return self._execute_rag_inference(
            message_job=self.message_job,
            conversation_id=conversation_id,
            content=content,
            provider=provider_name,
            model_name=model_name
        )