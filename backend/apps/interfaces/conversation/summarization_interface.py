"""
Summarization service interface module.
Abstract interface for document summarization.
"""

from abc import ABC, abstractmethod


class SummarizationServiceInterface(ABC):
    """
    Abstract interface for document summarization.
    Generates summaries using LLM.
    """

    @abstractmethod
    async def summarize_document(self, document, max_length=None):
        """
        Generate summary for document.

        Args:
            document: Document object with content
            max_length: Optional maximum summary length

        Returns:
            SummaryResult with summary_text and key_points
        """
        pass

    @abstractmethod
    async def create_bootstrap_message(self, conversation):
        """
        Create initial assistant message summarizing conversation documents.

        Args:
            conversation: Conversation object with attached documents

        Returns:
            Message object ready for storage
        """
        pass

    @abstractmethod
    def extract_key_points(self, text):
        """
        Extract key points from text.

        Args:
            text: Text to analyze

        Returns:
            List of key point strings
        """
        pass
