from typing import Any, Mapping

from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_provider import IProvider
from sys_services.read_config.read_chunking_config import CHUNKING_CONFIG
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_google_config import (
    GOOGLE_PICKER_CONFIG,
    INITIAL_API_BASE_URL,
)
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.read_config.read_list_provider import LIST_EMBEDDING_MODELS, LIST_MODELS, LIST_PROVIDERS
from sys_services.read_config.read_ollama_config import OLLAMA_CONFIG
from sys_services.read_config.read_qdrant_config import CLUSTER_CONFIG
from sys_services.read_config.read_redis_config import REDIS_CONFIG


class EnvConfigProvider(IConfigProvider):
    def get_initial_api_base_url(self) -> str:
        return INITIAL_API_BASE_URL

    def get_google_picker_config(self) -> Mapping[str, Any]:
        return dict(GOOGLE_PICKER_CONFIG)

    def get_mistral_config(self) -> Mapping[str, Any]:
        return dict(MISTRAL_CONFIG)

    def get_gemini_config(self) -> Mapping[str, Any]:
        return dict(GEMINI_EMBEDDING_CONFIG)

    def get_ollama_config(self) -> Mapping[str, Any]:
        return dict(OLLAMA_CONFIG)

    def get_qdrant_config(self) -> Mapping[str, Any]:
        return dict(CLUSTER_CONFIG)

    def get_chunking_config(self) -> Mapping[str, Any]:
        return dict(CHUNKING_CONFIG)

    def get_list_model_embedding(self) -> list[str]:
        return LIST_EMBEDDING_MODELS

    def get_list_models(self) -> list[str]:
        return LIST_MODELS
    
    def get_list_providers(self) -> list[IProvider]:
        return LIST_PROVIDERS

    def get_redis_config(self) -> Mapping[str, Any]:
        return dict(REDIS_CONFIG)


DEFAULT_CONFIG_PROVIDER = EnvConfigProvider()
