import numpy as np
from ollama import Client
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest, IEmbeddingResponse
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.core.interfaces.system.i_logging import ILogger
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings.ollama import OllamaEmbeddings

class OllamaClient(ILLMClient):

    def __init__(
        self,
        base_url: str,
        logger: ILogger,
        timeout: float
    ):
        if not base_url or base_url.strip() == "":
            raise ValueError("Base URL must be provided for OllamaClient.")
        self.host = base_url
        self.client = Client(host=self.host, timeout=timeout)
        self.timeout = timeout
        self.logger = logger

    def generate(self, request: ICompletionRequest, file_caller: str = "") -> str:
        self.logger.info(
            f"Sending request to Ollama: model={request.model}, prompt_length={len(request.prompt)}",
            source=str(self.__class__),
            call_by=file_caller,
            method_call=self.generate.__name__,
        )
        response = self.client.generate(
            model=request.model,
            prompt=request.prompt
        )
        values = response.response
        if values is None:
            self.logger.error("No response received from Ollama API.", source=str(self.__class__), call_by=file_caller, method_call=self.generate.__name__)
            raise ValueError("No response received from Ollama API.")
        self.logger.info(
            "Successfully generated content using Ollama API.",
            source=str(self.__class__),
            call_by=file_caller,
            method_call=self.generate.__name__
        )
        return response.response if response.response is not None else ""

    def embedding(self, request: ICompletionRequest, file_caller: str = "") -> IEmbeddingResponse:
        self.logger.info(
            "Generating embedding from Ollama API.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__
        )
        response = self.client.embed(
            model=request.model,
            input=request.prompt
        )
        if not response['embeddings']:
            self.logger.error("Response from Ollama API does not contain embeddings.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
            raise ValueError("Response from Ollama API does not contain embeddings.")
        self.logger.info("Successfully generated embedding using Ollama API.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
        values = response['embeddings'][0]
        if values is None:
            self.logger.error("Embedding response from Ollama API does not contain values.", source=str(self.__class__), call_by=file_caller, method_call=self.embedding.__name__)
            raise ValueError("Embedding response from Ollama API does not contain values.")
        return IEmbeddingResponse(embedding=np.array(values), dimensions=len(values), shape=(len(values),))

    def get_embedder_model(self, model: str, file_caller: str = "") -> Embedder:
        self.logger.info(
            "Retrieving embedder model from Ollama API.", source=str(self.__class__), call_by=file_caller, method_call=self.get_embedder_model.__name__
        )
        return OllamaEmbeddings(model, rate_limit_handler=None, host=self.host, timeout=self.timeout)

    def get_llm_model(self, model_name: str, file_caller: str = "") -> LLMInterface:
        self.logger.info(
            "Retrieving LLM model from Ollama API.", source=str(self.__class__), call_by=file_caller, method_call=self.get_llm_model.__name__
        )
        return OllamaLLM(model_name=model_name, host=self.host, timeout=self.timeout)


    def is_available(self, model: str, file_caller: str = "") -> bool:
        self.logger.info(
            "Checking Ollama API availability.", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
        )
        try:
            response = self.client.generate(
                model=model,
                prompt="Hello"
            )
            if response.response is not None:
                self.logger.info(
                    "Ollama API is available.", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
                )
                return True
            else:
                self.logger.error(
                    "Ollama API is not available: No response received.", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
                )
                return False
        except Exception as e:
            self.logger.error(
                f"Ollama API availability check failed: {str(e)}", source=str(self.__class__), call_by=file_caller, method_call=self.is_available.__name__
            )
            return False
