from abc import ABC, abstractmethod
from typing import Any, Mapping


class IConfigProvider(ABC):
    @abstractmethod
    def get_initial_api_base_url(self) -> str:
        pass

    @abstractmethod
    def get_google_picker_config(self) -> Mapping[str, Any]:
        pass

    @abstractmethod
    def get_mistral_config(self) -> Mapping[str, Any]:
        pass

    @abstractmethod
    def get_gemini_config(self) -> Mapping[str, Any]:
        pass

    @abstractmethod
    def get_ollama_config(self) -> Mapping[str, Any]:
        pass

    @abstractmethod
    def get_qdrant_config(self) -> Mapping[str, Any]:
        pass

    @abstractmethod
    def get_chunking_config(self) -> Mapping[str, Any]:
        pass

    @abstractmethod
    def get_embedding_provider(self) -> str:
        pass

    @abstractmethod
    def get_list_models(self) -> list[str]:
        pass
