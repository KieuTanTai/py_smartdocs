"""
Job management interface module.
Abstract interface for background job orchestration.
"""

from abc import ABC, abstractmethod


class IJobManagement(ABC):
    """
    Abstract interface for background job management.
    Orchestrates Celery task scheduling and monitoring.
    """

    @abstractmethod
    def schedule_document_processing(self, document_id):
        """
        Schedule document processing task.

        Task pipeline:
        - Extract content
        - Normalize text
        - Create chunks
        - Generate embeddings
        - Index to vector store
        - Generate summary

        Args:
            document_id: Document to process

        Returns:
            Task ID for tracking
        """
        pass

    @abstractmethod
    def schedule_conversation_preparation(self, conversation_id):
        """
        Schedule conversation preparation task.

        Task pipeline:
        - Verify attached documents are indexed
        - Generate bootstrap summary message
        - Update conversation status

        Args:
            conversation_id: Conversation to prepare

        Returns:
            Task ID for tracking
        """
        pass

    @abstractmethod
    def get_job_status(self, job_id):
        """
        Get current job status.

        Args:
            job_id: Task ID

        Returns:
            Status dict with state, progress, result, errors
        """
        pass

    @abstractmethod
    def cancel_job(self, job_id):
        """
        Cancel running or queued job.

        Args:
            job_id: Task ID

        Returns:
            Boolean success status
        """
        pass
