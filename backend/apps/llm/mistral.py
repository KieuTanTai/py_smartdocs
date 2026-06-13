import os

import ssl
import httpx
import numpy as np
from mistralai import Mistral
from backend.apps.core.interfaces.core.i_dataclass_transaction import (
    ICompletionRequest,
    IEmbeddingResponse,
)
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.core.interfaces.system.i_logging import ILogger
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.embeddings.mistral import MistralAIEmbeddings
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.llm import MistralAILLM

class MistralClient(ILLMClient):

    def __init__(
        self,
        api_key: str,
        logger: ILogger,
        timeout: float = 60.0,
    ):
        if (api_key is None) or (api_key.strip() == ""):
            raise ValueError("API key must be provided for MistralClient.")
        self.timeout = timeout
        self.logger = logger
        self.api_key = api_key
        self.client = Mistral(api_key=api_key)

    def generate(self, request: ICompletionRequest, file_caller: str = "") -> str:
        self.logger.info("Sending request to Mistral API.", source=str(self.__class__), call_by=file_caller, method_call=self.generate.__name__)
        response = self.client.chat.complete(
            model=request.model,
            messages=[{"role": "user", "content": request.prompt}]
        )
        if response.choices[0].message is None:
            self.logger.error("Response from Mistral API does not contain message.", source=str(self.__class__), call_by=file_caller, method_call=self.generate.__name__)
            raise ValueError("Response from Mistral API does not contain message.")
        self.logger.info("successfully generated content using Mistral API.", source=str(self.__class__), call_by=file_caller, method_call=self.generate.__name__)
        return str(response.choices[0].message.content)

    def embedding(self, request: ICompletionRequest, file_caller: str = "") -> IEmbeddingResponse:
        self.logger.info(
            "Generating embedding from Mistral API.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__
        )
        response = self.client.embeddings.create(
            model=request.model,
            inputs=[request.prompt],
        )
        if not response.data:
            self.logger.error("Response from Mistral API does not contain data.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
            raise ValueError("Response from Mistral API does not contain data.")
        self.logger.info("successfully generated embedding using Mistral API.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
        values = response.data[0].embedding
        if values is None:
            self.logger.error("Embedding response from Mistral API does not contain values.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
            raise ValueError("Embedding response from Mistral API does not contain values.")
        return IEmbeddingResponse(embedding=np.array(values), dimensions=len(values), shape=(len(values),))

    def get_embedder_model(self, model: str, file_caller: str = "") -> Embedder:
        self.logger.info(
            "Retrieving embedder model from Mistral API.", source=str(self.__class__), call_by=file_caller, method_call=self.get_embedder_model.__name__
        )
        return MistralAIEmbeddings(model, rate_limit_handler=None, api_key=self.api_key)

    def get_llm_model(self, model_name: str, file_caller: str = "") -> LLMInterface:
        self.logger.info(
            "Retrieving LLM model from Mistral API.", source=str(self.__class__), call_by=file_caller, method_call=self.get_llm_model.__name__
        )
        return MistralAILLM(model_name=model_name, api_key=self.api_key)

    def is_available(self, model: str, file_caller: str = "") -> bool:
        self.logger.info(
            "Checking Mistral API availability.", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
        )
        try:
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
