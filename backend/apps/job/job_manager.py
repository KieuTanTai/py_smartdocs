"""
Job manager module.
Orchestrates background job scheduling and monitoring.
"""

from backend.apps.job.conversation_job import ConversationJob
from backend.apps.job.upload_job import UploadJob
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.tasks.conversation_tasks import prepare_conversation as prepare_conversation_task
from celery.result import AsyncResult
from pathlib import Path


class JobManager:
    """
    Manages background job lifecycle.
    Schedules, monitors, and coordinates upload and conversation jobs.
    """

    def __init__(self, upload_job: UploadJob, conversation_job: ConversationJob):
        self.upload_job = upload_job
        self.conversation_job = conversation_job

    def schedule_document_processing(
        self,
        document_id: str,
        file_path: Path,
        provider: EProviderName,
    ):
        """Schedule upload/document processing flow."""
        return self.upload_job.run(document_id=document_id, file_path=file_path, provider=provider)

    def schedule_conversation_preparation(
        self,
        conversation_id: str,
        provider: EProviderName,
        model_name: str | None = None,
    ):
        """Schedule conversation preparation flow using Celery chain."""
        result = prepare_conversation_task.delay(
            conversation_id,
            provider.value,
            model_name,
        )
        return {"task_id": result.id}

    def get_job_status(self, job_id: str) -> dict:
        """Return current Celery job state, result, and error details."""
        result = AsyncResult(job_id)
        status = {
            "task_id": job_id,
            "state": result.state,
            "ready": result.ready(),
            "successful": result.successful(),
            "result": None,
            "traceback": None,
        }

        if result.ready():
            try:
                status["result"] = result.result
            except Exception as exc:
                status["result"] = None
                status["traceback"] = str(exc)

        if result.failed():
            status["traceback"] = getattr(result, "traceback", None)

        return status

    def cancel_job(self, job_id: str) -> dict:
        """Cancel a running or queued Celery job by id."""
        result = AsyncResult(job_id)
        try:
            result.revoke(terminate=True, signal='SIGTERM')
            return {
                "task_id": job_id,
                "cancelled": True,
                "state": result.state,
            }
        except Exception as exc:
            return {
                "task_id": job_id,
                "cancelled": False,
                "error": str(exc),
            }
