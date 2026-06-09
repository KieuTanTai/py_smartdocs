from abc import ABC, abstractmethod


#! NOTE: THIS INTERFACE NEED TO FIX RETURN TYPE
class IBaseJob(ABC):
    """Interface for background jobs."""
    """Base class for all background jobs."""

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
