"""
Document database service.
Concrete CRUD implementation for ConversationCacheModel.
"""

from pathlib import Path
from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from backend.apps.core.enums.e_document_status import EDocumentStatus
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_cache_database import (
    IConversationCacheDatabase,
)
from backend.apps.services.chat.models import ConversationModel, ConversationCacheModel


class ConversationCacheDatabaseService(IConversationCacheDatabase):
    """Django ORM implementation for conversation cache CRUD operations."""

    def create(self, **fields: Any) -> ConversationCacheModel:
        return ConversationCacheModel.objects.create(**fields)

    def create_conversation_cache(
        self,
        conversation: ConversationModel,
        file_path: str | Path | None = None,
        status: EDocumentStatus = EDocumentStatus.UPLOADED,
        content: str | None = None,
        is_active: bool = True,
        **extra_fields: Any,
    ) -> ConversationCacheModel:
        return self.create(
            conversation_cache_conversation=conversation,
            conversation_cache_file_path=str(file_path) if file_path is not None else None,
            conversation_cache_status=status,
            conversation_cache_is_active=is_active,
            **extra_fields,
        )

    def get_by_id(self, model_id: Any) -> ConversationCacheModel:
        return ConversationCacheModel.objects.get(pk=model_id)

    def get_by_ids(self, model_ids: list[Any]) -> QuerySet[ConversationCacheModel]:
        return ConversationCacheModel.objects.filter(pk__in=model_ids)

    def get_by_file_path(self, file_path: Path) -> QuerySet[ConversationCacheModel]:
        return ConversationCacheModel.objects.filter(conversation_cache_file_path=str(file_path))

    def get_by_file_paths(self, file_paths: list[Path]) -> QuerySet[ConversationCacheModel]:
        return ConversationCacheModel.objects.filter(
            conversation_cache_file_path__in=[str(path) for path in file_paths]
        )

    def get_by_conversation(self, conversation: ConversationModel) -> ConversationCacheModel:
        return ConversationCacheModel.objects.get(conversation_cache_conversation=conversation)

    def list(self, **filters: Any) -> QuerySet[ConversationCacheModel]:
        queryset = ConversationCacheModel.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.order_by("-conversation_cache_created_at")

    @transaction.atomic
    def update(self, model_id: Any, **fields: Any) -> ConversationCacheModel:
        document = self.get_by_id(model_id)

        for field_name, value in fields.items():
            if field_name == "file_path" and isinstance(value, Path):
                value = str(value)
            setattr(document, field_name, value)

        document.save(update_fields=list(fields.keys()))
        return document

    def update_status(self, document_id: Any, status: EDocumentStatus) -> ConversationCacheModel:
        return self.update(document_id, conversation_cache_status=status)

    def deactivate(self, document_id: Any) -> ConversationCacheModel:
        return self.update(document_id, conversation_cache_is_active=False)

    @transaction.atomic
    def delete(self, model_id: Any) -> int:
        deleted_count, _ = ConversationCacheModel.objects.filter(pk=model_id).delete()
        return deleted_count
