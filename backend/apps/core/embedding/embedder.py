"""
Text embedder module.
Generates embeddings for text chunks using various models.
"""

from backend.apps.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory


class Embedder:
    """
    Base class for text embedding generation.
    Provider-agnostic interface for embedding models.
    """

    def __init__(self, provider: ILLMProviderFactory):
        self.provider = provider

    def embed(self, text):
        # TODO: Generate embedding for single text
        # Returns: vector of floats
        pass

    def embed_batch(self, texts):
        # TODO: Generate embeddings for multiple texts
        # Returns: list of vectors
        pass

    def get_dimension(self):
        # TODO: Return embedding dimension size
        pass
