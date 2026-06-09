from pathlib import Path
from celery import current_app
from celery.result import AsyncResult

from backend.apps.core.enums.e_provider_name import EProviderName

from backend.apps.interfaces.job.i_job_management import IJobManagement
from backend.apps.interfaces.job.i_upload_job import IUploadJob
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.interfaces.job.i_message_job import IMessageJob

from backend.apps.tasks.document_tasks import DocumentTask
from backend.apps.tasks.conversation_tasks import ConversationTask
from backend.apps.tasks.message_tasks import MessageTask
from backend.apps.tasks.upload_tasks import UploadTask


class JobManager(IJobManagement):
    def __init__(
        self,
        upload_job: IUploadJob,
        conversation_job: IConversationJob,
        message_job: IMessageJob,
    ):
        self.upload_job = upload_job
        self.conversation_job = conversation_job
        self.message_job = message_job

    def schedule_document_processing(
        self, document_id: str, file_path: Path, provider: EProviderName
    ):
        result = current_app.send_task(
            UploadTask.name,
            obj={"document_id": document_id, "provider_name": provider.value},
        )
        return {"task_id": result.id}

    def schedule_conversation_preparation(
        self,
        conversation_id: str,
        provider: EProviderName,
        model_name: str | None = None,
    ):
        result = current_app.send_task(
            ConversationTask.name,
            obj={
                "conversation_id": conversation_id,
                "provider_name": provider.value,
                "model_name": model_name,
            },
        )
        return {"task_id": result.id}

    def execute_chat_message_async(
        self,
        conversation_id: str,
        content: str,
        provider: EProviderName,
        model_name: str | None = None,
    ):
        result = current_app.send_task(
            MessageTask.name,
            obj={
                "conversation_id": conversation_id,
                "content": content,
                "provider_name": provider.value,
                "model_name": model_name,
            },
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
            result.revoke(terminate=True, signal="SIGTERM")
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
