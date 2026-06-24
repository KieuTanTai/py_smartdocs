import os
import numpy as np
from google import genai
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest, IEmbeddingResponse
from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse, IGenerateResponseMetadata
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.core.interfaces.system.i_logging import ILogger
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.llm import VertexAILLM
from neo4j_graphrag.embeddings import VertexAIEmbeddings


class GeminiLLM(LLMInterface):
    """Custom wrapper for Gemini LLM to work with neo4j_graphrag."""
    
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
    
    def invoke(self, input: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[{"parts": [{"text": input}]}],
        )
        return response.text if response.text else ""


class GeminiEmbedder(Embedder):
    """Custom wrapper for Gemini embedder to work with neo4j_graphrag."""
    
    def __init__(self, model: str, rate_limit_handler=None, api_key: str = ""):
        super().__init__(model)
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.embedding_dim = 768  # Default dimension for Gemini embeddings
    
    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
        )
        if response.embeddings and response.embeddings[0].values:
            values = list(response.embeddings[0].values)
            self.embedding_dim = len(values)  # Update dimension based on actual response
            return values
        return []

class GeminiClient(ILLMClient):

    def __init__(
        self,
        api_key: str,
        logger: ILogger,
        timeout: float,
    ):
        if (api_key is None) or (api_key.strip() == ""):
            raise ValueError("API key must be provided for GeminiClient.")
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.timeout = timeout
        self.logger = logger

    def generate(self, request: ICompletionRequest, file_caller: str = "") -> IGenerateResponse:
        self.logger.info("Sending request to Gemini API.", source=str(self.__class__), call_by=file_caller, method_call=self.generate.__name__)

        response = self.client.models.generate_content(
            model=request.model,
            contents=[{"parts": [{"text": request.prompt}]}],
        )
        if response.text is None:
            self.logger.error("Response from Gemini API does not contain text.", source=str(self.__class__), call_by=file_caller, method_call=self.generate.__name__)
            raise ValueError("Response from Gemini API does not contain text.")
        self.logger.info("successfully generated content using Gemini API.", source=str(self.__class__), call_by=file_caller, method_call=self.generate.__name__)
        return IGenerateResponse(
            content=response.text,
            model_name=request.model,
        )


    def embedding(self, request: ICompletionRequest, file_caller: str = "") -> IEmbeddingResponse:
        self.logger.info(
            "Generating embedding from Gemini API.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__
        )
        response = self.client.models.embed_content(
            model=request.model,
            contents=request.prompt,
        )
        if not response.embeddings:
            self.logger.error("Response from Gemini API does not contain embeddings.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
            raise ValueError("Response from Gemini API does not contain embeddings.")
        self.logger.info("successfully generated embedding using Gemini API.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
        values = response.embeddings[0].values
        if values is None:
            self.logger.error("Embedding response from Gemini API does not contain values.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
            raise ValueError("Embedding response from Gemini API does not contain values.")
        return IEmbeddingResponse(embedding=np.array(values), dimensions=len(values), shape=(len(values),))

    def get_embedder_model(self, model: str, file_caller: str = "") -> Embedder:
        self.logger.info(
            "Retrieving embedder model from Gemini API.", source=str(self.__class__), call_by=file_caller, method_call=self.get_embedder_model.__name__
        )
        return GeminiEmbedder(model, rate_limit_handler=None, api_key=self.api_key)

    def get_llm_model(self, model_name: str, file_caller: str = "") -> LLMInterface:
        self.logger.info(
            "Retrieving LLM model from Gemini API.", source=str(self.__class__), call_by=file_caller, method_call=self.get_llm_model.__name__
        )
        return GeminiLLM(model_name=model_name, api_key=self.api_key)


    def is_available(self, model: str, file_caller: str = "") -> bool:
        self.logger.info(
            "Checking Gemini API availability.", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
        )
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[{"parts": [{"text": "Hello"}]}],
            )
            if response.text is not None:
                self.logger.info(
                    "Gemini API is available.", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
                )
                return True
            else:
                self.logger.error(
                    "Gemini API is not available: No text in response.", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
                )
                return False
        except Exception as e:
            self.logger.error(
                f"Error occurred while checking Gemini API availability: {e}",
                source=str(self.__class__),
                call_by=file_caller,
                method_call=self.is_available.__name__,
            )
            return False
