"""
Job Manager with Factory Pattern.
Orchestrates background job scheduling and monitoring.
"""

from backend.apps.job.conversation_job import ConversationJob
from backend.apps.job.upload_job import UploadJob
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.tasks.conversation_tasks import prepare_conversation as prepare_conversation_task
from celery.result import AsyncResult
from pathlib import Path
from typing import Dict, Any, Optional, Type
from uuid import UUID
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Enumeration of available job types."""
    DOCUMENT_UPLOAD = "document_upload"
    MESSAGE_PROCESS = "message_process"
    CONVERSATION_PREPARE = "conversation_prepare"
    DELETE_CONVERSATION = "delete_conversation"


class BaseJob:
    """Base class for all background jobs."""

    def __init__(self, job_id: Optional[UUID] = None):
        """
        Initialize base job.

        Args:
            job_id: Optional UUID for the job (auto-generated if not provided)
        """
        self.job_id = job_id or uuid.uuid4()
        self.status = "pending"  # pending, running, completed, failed
        self.result = None
        self.error = None
        self.logger = logger

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the job (to be implemented by subclasses).

        Args:
            **kwargs: Job-specific parameters

        Returns:
            Dictionary with execution results
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current job status.

        Returns:
            Dictionary with job status and metadata
        """
        return {
            "job_id": str(self.job_id),
            "job_type": self.__class__.__name__,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class DocumentUploadJob(BaseJob):
    """Background job for document upload and processing."""

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute document upload job.

        Args:
            file_id: UUID of the document
            file_path: Path to the file
            conversation_id: Optional conversation ID

        Returns:
            Dictionary with upload results
        """
        try:
            self.status = "running"
            
            file_id = kwargs.get("file_id")
            file_path = kwargs.get("file_path")
            conversation_id = kwargs.get("conversation_id")

            self.logger.info(
                f"Processing document upload job {self.job_id}: file_id={file_id}"
            )

            # This will be coordinated with actual task execution
            # For now, just mark as ready for task pipeline
            self.result = {
                "file_id": file_id,
                "conversation_id": conversation_id,
                "status": "queued_for_processing",
                "job_id": str(self.job_id),
            }
            self.status = "completed"

            return self.result

        except Exception as e:
            self.logger.error(f"Error in document upload job: {e}")
            self.status = "failed"
            self.error = str(e)
            raise


class MessageProcessJob(BaseJob):
    """Background job for message processing and response generation."""

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute message processing job.

        Args:
            conversation_id: UUID of conversation
            user_message_id: UUID of user message
            user_input: User message text
            provider: LLM provider
            model: Model name

        Returns:
            Dictionary with message processing results
        """
        try:
            self.status = "running"

            conversation_id = kwargs.get("conversation_id")
            user_message_id = kwargs.get("user_message_id")
            user_input = kwargs.get("user_input")
            provider = kwargs.get("provider")
            model = kwargs.get("model")

            self.logger.info(
                f"Processing message job {self.job_id}: "
                f"conversation_id={conversation_id}, model={model}"
            )

            # This will be coordinated with actual task execution
            self.result = {
                "conversation_id": str(conversation_id),
                "user_message_id": str(user_message_id),
                "status": "queued_for_retrieval",
                "job_id": str(self.job_id),
            }
            self.status = "completed"

            return self.result

        except Exception as e:
            self.logger.error(f"Error in message process job: {e}")
            self.status = "failed"
            self.error = str(e)
            raise


class ConversationPrepareJob(BaseJob):
    """Background job for conversation preparation."""

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute conversation preparation job.

        Args:
            conversation_id: UUID of conversation
            document_ids: List of document UUIDs

        Returns:
            Dictionary with preparation results
        """
        try:
            self.status = "running"

            conversation_id = kwargs.get("conversation_id")
            document_ids = kwargs.get("document_ids", [])

            self.logger.info(
                f"Preparing conversation job {self.job_id}: "
                f"conversation_id={conversation_id}, documents={len(document_ids)}"
            )

            # Check all documents are indexed
            self.result = {
                "conversation_id": str(conversation_id),
                "documents_count": len(document_ids),
                "status": "ready",
                "job_id": str(self.job_id),
            }
            self.status = "completed"

            return self.result

        except Exception as e:
            self.logger.error(f"Error in conversation prepare job: {e}")
            self.status = "failed"
            self.error = str(e)
            raise


class DeleteConversationJob(BaseJob):
    """Background job for conversation deletion with cleanup."""

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute conversation deletion job (transactional).

        Args:
            conversation_id: UUID of conversation

        Returns:
            Dictionary with deletion results
        """
        try:
            self.status = "running"

            conversation_id = kwargs.get("conversation_id")

            self.logger.info(
                f"Deleting conversation job {self.job_id}: conversation_id={conversation_id}"
            )

            # This will handle transactional deletion with FAISS cleanup
            self.result = {
                "conversation_id": str(conversation_id),
                "status": "queued_for_deletion",
                "job_id": str(self.job_id),
            }
            self.status = "completed"

            return self.result

        except Exception as e:
            self.logger.error(f"Error in delete conversation job: {e}")
            self.status = "failed"
            self.error = str(e)
            raise


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
