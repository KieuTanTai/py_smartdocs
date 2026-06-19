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
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel


class ConversationFileDatabaseService(IConversationFileDatabase):
    """Django ORM implementation for conversation file CRUD operations."""

    def create(self, **fields: Any) -> ConversationFilesModel:
        return ConversationFilesModel.objects.create(**fields)

    def create_conversation_file(
        self,
        conversation: ConversationModel,
        cloud_id: str,
        **extra_fields: Any,
    ) -> ConversationFilesModel:
        return self.create(
            conversation=conversation,
            conversation_files_cloud_id=cloud_id,
            **extra_fields,
        )

    def get_by_id(self, model_id: Any) -> ConversationFilesModel:
        return ConversationFilesModel.objects.get(pk=model_id)

    def get_by_conversation(
        self, conversation: ConversationModel
    ) -> QuerySet[ConversationFilesModel]:
        return ConversationFilesModel.objects.filter(conversation=conversation)

    def get_by_cloud_id(self, cloud_id: str) -> QuerySet[ConversationFilesModel]:
        return ConversationFilesModel.objects.filter(conversation_files_cloud_id=cloud_id)

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
    def delete_by_conversation(self, conversation: ConversationModel) -> int:
        deleted_count, _ = ConversationFilesModel.objects.filter(
            conversation=conversation
        ).delete()
        return deleted_count
