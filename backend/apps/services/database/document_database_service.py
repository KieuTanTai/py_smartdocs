"""
Document database service.
Concrete CRUD implementation for DocumentModel.
"""

from pathlib import Path
from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from backend.apps.core.enums.e_document_status import EDocumentStatus
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import (
    IDocumentDatabase,
)
from backend.apps.services.chat.models import ConversationModel, DocumentModel


class DocumentDatabaseService(IDocumentDatabase):
    """Django ORM implementation for document CRUD operations."""

    def create(self, **fields: Any) -> DocumentModel:
        return DocumentModel.objects.create(**fields)

    def create_document(
        self,
        conversation: ConversationModel,
        file_path: str | Path | None = None,
        status: EDocumentStatus = EDocumentStatus.UPLOADED,
        content: str | None = None,
        is_active: bool = True,
        **extra_fields: Any,
    ) -> DocumentModel:
        return self.create(
            documents_conversation=conversation,
            documents_file_path=str(file_path) if file_path is not None else None,
            documents_status=status,
            documents_content=content,
            documents_is_active=is_active,
            **extra_fields,
        )

    def get_by_id(self, model_id: Any) -> DocumentModel:
        return DocumentModel.objects.get(pk=model_id)

    def get_by_ids(self, model_ids: list[Any]) -> QuerySet[DocumentModel]:
        return DocumentModel.objects.filter(pk__in=model_ids)

    def get_by_file_path(self, file_path: Path) -> QuerySet[DocumentModel]:
        return DocumentModel.objects.filter(documents_file_path=str(file_path))

    def get_by_file_paths(self, file_paths: list[Path]) -> QuerySet[DocumentModel]:
        return DocumentModel.objects.filter(documents_file_path__in=[str(path) for path in file_paths])

    def get_by_conversation(self, conversation: ConversationModel) -> DocumentModel:
        return DocumentModel.objects.get(documents_conversation=conversation)

    def list(self, **filters: Any) -> QuerySet[DocumentModel]:
        queryset = DocumentModel.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.order_by("-documents_created_at")

    @transaction.atomic
    def update(self, model_id: Any, **fields: Any) -> DocumentModel:
        document = self.get_by_id(model_id)

        for field_name, value in fields.items():
            if field_name == "file_path" and isinstance(value, Path):
                value = str(value)
            setattr(document, field_name, value)

        document.save(update_fields=list(fields.keys()))
        return document

    def update_status(self, document_id: Any, status: EDocumentStatus) -> DocumentModel:
        return self.update(document_id, documents_status=status)

    def deactivate(self, document_id: Any) -> DocumentModel:
        return self.update(document_id, documents_is_active=False)

    @transaction.atomic
    def delete(self, model_id: Any) -> int:
        deleted_count, _ = DocumentModel.objects.filter(pk=model_id).delete()
        return deleted_count
