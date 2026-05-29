"""
Graph service interface module.
Abstract interface for graph-based document processing.
"""

from abc import ABC, abstractmethod


class IGraphService(ABC):
    """
    Abstract interface for graph-based document processing.
    Builds and queries knowledge graphs from documents.
    """

    @abstractmethod
    async def build_document_graph(self, document):
        """
        Build knowledge graph from document.

        Args:
            document: Document object

        Returns:
            Graph representation with nodes and edges
        """
        pass

    @abstractmethod
    async def extract_entities(self, text):
        """
        Extract entities and relationships from text.

        Args:
            text: Text to analyze

        Returns:
            List of Entity and Relationship objects
        """
        pass

    @abstractmethod
    async def graph_search(self, query, document_ids):
        """
        Search using graph traversal.

        Args:
            query: Search query
            document_ids: Scope to specific documents

        Returns:
            List of results from graph traversal
        """
        pass
