import httpx
import numpy as np
from mistralai.client import Mistral
from backend.apps.core.interfaces.core.i_dataclass_transaction import (
    ICompletionRequest,
    IEmbeddingResponse,
)
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.core.interfaces.system.i_logging import ILogger


class MistralClient(ILLMClient):

    def __init__(
        self,
        api_key: str,
        logger: ILogger,
        timeout: float
    ):
        if (api_key is None) or (api_key.strip() == ""):
            raise ValueError("API key must be provided for MistralClient.")
        self.client = Mistral(api_key=api_key)
        self.timeout = timeout
        self.logger = logger

    def generate(self, request: ICompletionRequest) -> str:
        self.logger.info("Sending request to Mistral API.", source=str(self.__class__))
        response = self.client.chat.complete(
            model=request.model,
            messages=[{"role": "user", "content": request.prompt}]
        )
        if response.choices[0].message is None:
            self.logger.error("Response from Mistral API does not contain message.", source=str(self.__class__))
            raise ValueError("Response from Mistral API does not contain message.")
        self.logger.info("successfully generated content using Mistral API.", source=str(self.__class__))
        return str(response.choices[0].message.content)


    def embedding(self, request: ICompletionRequest) -> IEmbeddingResponse:
        self.logger.info(
            "Generating embedding from Mistral API.", source=str(self.__class__)
        )
        response = self.client.embeddings.create(
            model=request.model,
            inputs=[request.prompt],
        )
        if not response.data:
            self.logger.error("Response from Mistral API does not contain data.", source=str(self.__class__))
            raise ValueError("Response from Mistral API does not contain data.")
        self.logger.info("successfully generated embedding using Mistral API.", source=str(self.__class__))
        values = response.data[0].embedding
        if values is None:
            self.logger.error("Embedding response from Mistral API does not contain values.", source=str(self.__class__))
            raise ValueError("Embedding response from Mistral API does not contain values.")
        return IEmbeddingResponse(embedding=np.array(values), dimensions=len(values), shape=(len(values),))


    def is_available(self, model: str) -> bool:
        self.logger.info(
            "Checking Mistral API availability.", source=str(self.__class__)
        )
        
        try:
            # Perform a simple API call to check availability
            response = self.client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return response.choices[0].message is not None
        except Exception as e:
            self.logger.error(
                f"Mistral API is not available: {str(e)}", source=str(self.__class__)
            )
            return False
