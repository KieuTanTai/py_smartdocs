from pathlib import Path
from typing import Any

from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider


def get_instance_model_database(model_type: Any, database_provider: IDatabaseProvider) -> object:
    """Get the instance of the model database service."""
    document_database = database_provider.get_model_service(model_type)
    if document_database is None:
        raise ValueError(f"Document database service for {model_type.__name__} is not available.")
    return document_database