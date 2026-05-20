"""
Embedder interface module.
Abstract interface for text embedding generation.
"""

from abc import ABC, abstractmethod


class IEmbedder(ABC):
    """
    Abstract interface for text embedding.
    Generates vector embeddings for text using various models.
    """

    @abstractmethod
    async def embed(self, text):
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Vector of floats (embedding)
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts):
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of text strings

        Returns:
            List of vectors (embeddings)
        """
        pass

    @abstractmethod
    def get_dimension(self):
        """
        Get embedding vector dimension size.

        Returns:
            Integer dimension (e.g., 384, 768)
        """
        pass
