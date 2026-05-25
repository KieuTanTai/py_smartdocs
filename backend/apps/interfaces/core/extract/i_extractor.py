"""
Extract service interface module.
Abstract interface for selecting the right extraction path.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from backend.apps.interfaces.services.chat.i_completion import ICompletionResponse


class IExtractor(ABC):
    """
    Abstract interface for extracting content from a file.
    """

    @abstractmethod
    async def extract(self, file_path: Path) -> ICompletionResponse:
        """
        Extract content from a file path.

        Args:
            file_path: Path to input file

        Returns:
            ICompletionResponse: Response object with extracted content
        """
        pass
