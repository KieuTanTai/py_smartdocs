import os
import numpy as np
from google import genai
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest, IEmbeddingResponse
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.core.interfaces.system.i_logging import ILogger

class GeminiClient(ILLMClient):

    def __init__(
        self,
        api_key: str,
        logger: ILogger,
        timeout: float,
    ):
        if (api_key is None) or (api_key.strip() == ""):
            raise ValueError("API key must be provided for GeminiClient.")
        self.client = genai.Client(api_key=api_key)
        self.timeout = timeout
        self.logger = logger

    def generate(self, request: ICompletionRequest) -> str:
        self.logger.info("Sending request to Gemini API.", source=str(self.__class__))

        response = self.client.models.generate_content(
            model=request.model,
            contents=[{"parts": [{"text": request.prompt}]}],
        )
        if response.text is None:
            self.logger.error("Response from Gemini API does not contain text.", source=str(self.__class__))
            raise ValueError("Response from Gemini API does not contain text.")
        self.logger.info("successfully generated content using Gemini API.", source=str(self.__class__))
        return response.text

    def embedding(self, request: ICompletionRequest) -> IEmbeddingResponse:
        self.logger.info(
            "Generating embedding from Gemini API.", source=str(self.__class__)
        )
        response = self.client.models.embed_content(
            model=request.model,
            contents=request.prompt,
        )
        if not response.embeddings:
            self.logger.error("Response from Gemini API does not contain embeddings.", source=str(self.__class__))
            raise ValueError("Response from Gemini API does not contain embeddings.")
        self.logger.info("successfully generated embedding using Gemini API.", source=str(self.__class__))
        values = response.embeddings[0].values
        if values is None:
            self.logger.error("Embedding response from Gemini API does not contain values.", source=str(self.__class__))
            raise ValueError("Embedding response from Gemini API does not contain values.")
        return IEmbeddingResponse(embedding=np.array(values), dimensions=len(values), shape=(len(values),))

    def is_available(self, model: str) -> bool:
        self.logger.info(
            "Checking Gemini API availability.", source=str(self.__class__)
        )
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[{"parts": [{"text": "Hello"}]}],
            )
            if response.text is not None:
                self.logger.info(
                    "Gemini API is available.", source=str(self.__class__)
                )
                return True
            else:
                self.logger.error(
                    "Gemini API is not available: No text in response.", source=str(self.__class__)
                )
                return False
        except Exception as e:
            self.logger.error(
                f"Error occurred while checking Gemini API availability: {e}",
                source=str(self.__class__),
            )
            return False
