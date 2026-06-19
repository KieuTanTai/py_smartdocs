"""
Database provider interface.
Resolves model database services by Django model type.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

from django.db.models import Model

from backend.apps.core.interfaces.services.rag_base.database.i_model_database import (
    IModelDatabase,
)


TModel = TypeVar("TModel", bound=Model)


class IDatabaseProvider(ABC):
    """Abstract provider for model database services."""

    @abstractmethod
    def get_model_service(self, model_type: type[TModel]) -> IModelDatabase[TModel]:
        """
        Return the database service registered for the given Django model type.

        Example:
            document_database = provider.get_model_service(DocumentModel)
        """
        pass
    