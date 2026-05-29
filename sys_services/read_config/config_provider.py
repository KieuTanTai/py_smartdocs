from typing import Any, Mapping

from backend.apps.core.interfaces.system.i_config import IConfigProvider
from sys_services.read_config.read_chunking_config import CHUNKING_CONFIG
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_google_config import (
    GOOGLE_PICKER_CONFIG,
    INITIAL_API_BASE_URL,
)
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.read_config.read_models import EMBEDDING_PROVIDER, LIST_MODELS
from sys_services.read_config.read_ollama_config import OLLAMA_CONFIG
from sys_services.read_config.read_qdrant_config import CLUSTER_CONFIG


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

    def get_embedding_provider(self) -> str:
        return EMBEDDING_PROVIDER

    def get_list_models(self) -> list[str]:
        return list(LIST_MODELS)


DEFAULT_CONFIG_PROVIDER = EnvConfigProvider()
