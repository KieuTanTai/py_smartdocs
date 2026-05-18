

class GeminiEmbedding: 
    def __init__(self, model_name: str = "gemini-1.5-pro", **kwargs):
        self.model_name = model_name
        # Initialize the Gemini embedding model here using the model_name and any additional kwargs

    def embed(self, text: str) -> list:
        # Implement the logic to generate embeddings for the input text using the Gemini model
        # Return the embeddings as a list (or any appropriate format)
        pass