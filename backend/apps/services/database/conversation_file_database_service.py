"""
Conversation file database service.
Concrete CRUD implementation for ConversationFilesModel.
"""

from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from backend.apps.core.interfaces.services.rag_base.database.i_conversation_file_database import (
    IConversationFileDatabase,
)
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, DocumentModel


class ConversationFileDatabaseService(IConversationFileDatabase):
    """Django ORM implementation for conversation file CRUD operations."""

    def create(self, **fields: Any) -> ConversationFilesModel:
        return ConversationFilesModel.objects.create(**fields)

    def create_conversation_file(
        self,
        document: DocumentModel,
        cloud_id: str,
        **extra_fields: Any,
    ) -> ConversationFilesModel:
        return self.create(
            conversation_files_document=document,
            conversation_files_cloud_id=cloud_id,
            **extra_fields,
        )

    def create_conversation_files_bulk(
        self,
        document_cloud_id_pairs: list[tuple[DocumentModel, str]],
        **extra_fields: Any,
    ) -> list[ConversationFilesModel]:
        conversation_files = [
            ConversationFilesModel(
                conversation_files_document=document,
                conversation_files_cloud_id=cloud_id,
                **extra_fields,
            )
            for document, cloud_id in document_cloud_id_pairs
        ]
        return ConversationFilesModel.objects.bulk_create(conversation_files)

    def get_by_id(self, model_id: Any) -> ConversationFilesModel:
        return ConversationFilesModel.objects.get(pk=model_id)

    def get_by_ids(self, model_ids: list[Any]) -> QuerySet[ConversationFilesModel]:
        return ConversationFilesModel.objects.filter(pk__in=model_ids)

    def get_by_cloud_ids(self, cloud_ids: list[str]) -> QuerySet[ConversationFilesModel]:
        return ConversationFilesModel.objects.filter(conversation_files_cloud_id__in=cloud_ids)

    def get_by_document(
        self, document: DocumentModel
    ) -> QuerySet[ConversationFilesModel]:
        return ConversationFilesModel.objects.filter(conversation_files_document=document)

    def get_by_cloud_id(self, cloud_id: str) -> QuerySet[ConversationFilesModel]:
        return ConversationFilesModel.objects.filter(conversation_files_cloud_id=cloud_id)

    def get_by_conversation(self, conversation: ConversationModel) -> QuerySet[ConversationFilesModel]:
        document = DocumentModel.objects.get(document_conversation=conversation)
        return ConversationFilesModel.objects.filter(conversation_files_document=document)

    def list(self, **filters: Any) -> QuerySet[ConversationFilesModel]:
        queryset = ConversationFilesModel.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.order_by("-conversation_files_uploaded_at")

    @transaction.atomic
    def update(self, model_id: Any, **fields: Any) -> ConversationFilesModel:
        conversation_file = self.get_by_id(model_id)

        for field_name, value in fields.items():
            setattr(conversation_file, field_name, value)

        conversation_file.save(update_fields=list(fields.keys()))
        return conversation_file

    @transaction.atomic
    def delete(self, model_id: Any) -> int:
        deleted_count, _ = ConversationFilesModel.objects.filter(pk=model_id).delete()
        return deleted_count

    @transaction.atomic
    def delete_by_document(self, document: DocumentModel) -> int:
        deleted_count, _ = ConversationFilesModel.objects.filter(
            conversation_files_document=document
        ).delete()
        return deleted_count
