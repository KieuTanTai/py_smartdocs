
from abc import ABC, abstractmethod


class INormalize(ABC):
    @abstractmethod
    def normalize(self, content: str) -> str:
        """
        Normalize the extracted content.

        Args:
            content: The raw extracted content to be normalized.

        Returns:
            str: The normalized content.
        """
        pass