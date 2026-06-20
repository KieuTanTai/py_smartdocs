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
from backend.apps.core.interfaces.dataclass.job.i_message_job import IMessageJobResponse
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.job.i_message_job import IMessageJob
from backend.apps.interfaces.tasks.i_message_task import IMessageTask
from sys_services.time_counter import TimeCounter

class MessageTask(Task, IMessageTask):

    def __init__(self, message_job: IMessageJob, logger: ILogger, time_counter: TimeCounter):
        self.message_job = message_job
        self.logger = logger
        self.time_counter = time_counter

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
        self.time_counter.reset()
        self.time_counter.start()
        
        result = self._execute_rag_inference(
            message_job=self.message_job,
            conversation_id=conversation_id,
            content=content,
            provider=provider_name,
            model_name=model_name
        )
            
        # CHỐT THỜI GIAN
        elapsed = self.time_counter.get_elapsed_time_ms()
        self.logger.info(f"MessageTask completed total End-to-End execution in {elapsed:.2f}ms for conversation {conversation_id}")
        
        # Ghi đè Latency = Tổng thời gian chạy của cả Task
        result.latency_ms = int(elapsed)
        
        return result