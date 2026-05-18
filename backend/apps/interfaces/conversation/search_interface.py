"""
Search service interface module.
Abstract interface for document search and retrieval.
"""

from abc import ABC, abstractmethod


class SearchServiceInterface(ABC):
    """
    Abstract interface for document search.
    Performs similarity search across document corpus using vector embeddings.
    """

    @abstractmethod
    async def search(self, query, document_ids, limit=5, filters=None):
        """
        Search for relevant chunks.

        Args:
            query: Search query string
            document_ids: List of document IDs to scope search
            limit: Maximum number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchHit objects with chunk content and relevance scores
        """
        pass

    @abstractmethod
    def build_search_context(self, search_hits):
        """
        Combine search hits into prompt context.

        Args:
            search_hits: List of SearchHit objects

        Returns:
            Formatted context string for LLM prompt
        """
        pass

    @abstractmethod
    def rank_results(self, hits, relevance_threshold=0.0):
        """
        Rank and filter search results.

        Args:
            hits: List of search results
            relevance_threshold: Minimum relevance score

        Returns:
            Filtered and ranked list of results
        """
        pass
