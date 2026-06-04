from abc import ABC, abstractmethod
from typing import Any, Mapping

from backend.apps.core.interfaces.system.i_provider import IProvider


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
    def get_list_model_embedding(self) -> list[str]:
        pass

    @abstractmethod
    def get_list_models(self) -> list[str]:
        pass

    @abstractmethod
    def get_list_providers(self) -> list[IProvider]:
        pass



