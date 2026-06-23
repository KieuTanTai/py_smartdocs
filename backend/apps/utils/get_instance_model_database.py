from pathlib import Path
from typing import Any

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.system.i_config import IConfigProvider


def get_instance_model_database(model_type: Any, database_provider: IDatabaseProvider) -> object:
    """Get the instance of the model database service."""
    document_database = database_provider.get_model_service(model_type)
    if document_database is None:
        raise ValueError(f"Document database service for {model_type.__name__} is not available.")
    return document_database

def get_embedding_model(config_provider: IConfigProvider, provider: EProviderName) -> str:
    for provider_record in config_provider.get_list_providers():
        if provider_record.provider_name == provider:
            return provider_record.embed_model_name
    raise ValueError(f"Embedding model not configured for provider {provider}")