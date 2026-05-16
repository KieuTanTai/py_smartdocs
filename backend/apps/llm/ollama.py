"""
Ollama LLM provider client.
Local or remote Ollama integration.
"""


class OllamaClient:
    """
    Ollama LLM client.
    Handles text generation using local or remote Ollama instance.
    """

    def __init__(self):
        # TODO: Initialize Ollama client with base URL and model
        pass

    async def generate(self, completion_request):
        # TODO: Call Ollama API for text generation
        # Returns: CompletionResponse with text, tokens, latency
        pass

    def get_model_info(self):
        # TODO: Return Ollama model configuration and capabilities
        pass

    def is_available(self):
        # TODO: Check if Ollama server is reachable
        pass
