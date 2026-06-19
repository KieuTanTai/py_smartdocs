"""
Generic database service interface.
Defines CRUD behavior shared by Django model database services.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from django.db.models import Model, QuerySet


TModel = TypeVar("TModel", bound=Model)


class IModelDatabase(ABC, Generic[TModel]):
    """Abstract CRUD interface for a Django model."""

    @abstractmethod
    def create(self, **fields: Any) -> TModel:
        """Create and return a model instance."""
        pass

    @abstractmethod
    def get_by_id(self, model_id: Any) -> TModel:
        """Get one model instance by primary key."""
        pass

    @abstractmethod 
    def get_by_ids(self, model_ids: list[Any]) -> QuerySet[TModel]:
        """Get multiple model instances by primary keys."""
        pass

    @abstractmethod
    def list(self, **filters: Any) -> QuerySet[TModel]:
        """List model instances, optionally filtered by model fields."""
        pass

    @abstractmethod
    def update(self, model_id: Any, **fields: Any) -> TModel:
        """Update one model instance by primary key."""
        pass

    @abstractmethod
    def delete(self, model_id: Any) -> int:
        """Delete one model instance by primary key and return deleted row count."""
        pass
