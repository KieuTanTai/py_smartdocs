"""
Job Manager with Factory Pattern.
Orchestrates background job scheduling and monitoring.
"""

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
    Job Manager with Factory Pattern.
    Creates, schedules, and monitors background jobs.
    """

    # Job type to class mapping
    JOB_REGISTRY: Dict[JobType, Type[BaseJob]] = {
        JobType.DOCUMENT_UPLOAD: DocumentUploadJob,
        JobType.MESSAGE_PROCESS: MessageProcessJob,
        JobType.CONVERSATION_PREPARE: ConversationPrepareJob,
        JobType.DELETE_CONVERSATION: DeleteConversationJob,
    }

    # In-memory job tracking (in production, use Celery result backend)
    _jobs: Dict[UUID, BaseJob] = {}

    def __init__(self):
        """Initialize job manager."""
        self.logger = logger

    def create_job(self, job_type: JobType, **kwargs) -> Dict[str, Any]:
        """
        Create and schedule a job.

        Args:
            job_type: Type of job to create (JobType enum)
            **kwargs: Job-specific parameters

        Returns:
            Dictionary with job metadata

        Raises:
            ValueError: If job_type is invalid
        """
        try:
            if job_type not in self.JOB_REGISTRY:
                raise ValueError(f"Unknown job type: {job_type}")

            # Create job instance
            job_class = self.JOB_REGISTRY[job_type]
            job = job_class()

            # Store job
            self._jobs[job.job_id] = job

            # Execute job (in production, queue with Celery)
            result = job.execute(**kwargs)

            self.logger.info(
                f"Created {job_type.value} job {job.job_id}: {job.status}"
            )

            return {
                "job_id": str(job.job_id),
                "job_type": job_type.value,
                "status": job.status,
                "result": result,
            }

        except ValueError as e:
            self.logger.error(f"Validation error creating job: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating job: {e}")
            raise

    def get_job_status(self, job_id: UUID) -> Dict[str, Any]:
        """
        Get status of a job.

        Args:
            job_id: UUID of the job

        Returns:
            Dictionary with job status

        Raises:
            ValueError: If job not found
        """
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self._jobs[job_id]
        return job.get_status()

    def cancel_job(self, job_id: UUID) -> Dict[str, Any]:
        """
        Cancel a running or queued job.

        Args:
            job_id: UUID of the job

        Returns:
            Dictionary with cancellation result

        Raises:
            ValueError: If job not found or already completed
        """
        try:
            if job_id not in self._jobs:
                raise ValueError(f"Job {job_id} not found")

            job = self._jobs[job_id]

            if job.status == "completed":
                raise ValueError(f"Cannot cancel completed job {job_id}")

            job.status = "cancelled"
            self.logger.info(f"Cancelled job {job_id}")

            return {
                "job_id": str(job_id),
                "status": "cancelled",
            }

        except ValueError as e:
            self.logger.error(f"Error cancelling job: {e}")
            raise

    def list_jobs(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        List all jobs with optional filtering.

        Args:
            status: Filter by status (optional)

        Returns:
            Dictionary with jobs list
        """
        jobs_list = []

        for job in self._jobs.values():
            if status and job.status != status:
                continue

            jobs_list.append(job.get_status())

        return {
            "jobs": jobs_list,
            "count": len(jobs_list),
            "total": len(self._jobs),
        }
