"""
Conversation database service.
Concrete CRUD implementation for ConversationModel.
"""

from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import (
    IConversationDatabase,
)
from backend.apps.services.chat.models import ConversationModel, DocumentModel


class ConversationDatabaseService(IConversationDatabase):
    """Django ORM implementation for conversation CRUD operations."""

    def create(self, **fields: Any) -> ConversationModel:
        return ConversationModel.objects.create(**fields)

    def create_conversation(
        self,
        conversations_name: str = "",
        conversations_title: str = "",
        **extra_fields: Any,
    ) -> ConversationModel:
        return self.create(
            conversations_name=conversations_name,
            conversations_title=conversations_title,
            **extra_fields,
        )

    def get_all(self) -> QuerySet[ConversationModel]:
        return ConversationModel.objects.all()

    def get_by_id(self, model_id: Any) -> ConversationModel:
        return ConversationModel.objects.get(pk=model_id)

    def get_by_ids(self, model_ids: list[Any]) -> QuerySet[ConversationModel]:
        return ConversationModel.objects.filter(pk__in=model_ids)

    def get_by_name(self, conversations_name: str) -> QuerySet[ConversationModel]:
        return ConversationModel.objects.filter(conversations_name=conversations_name)

    def get_by_document(self, document: DocumentModel) -> QuerySet[ConversationModel]:
        return ConversationModel.objects.filter(conversations_faiss_index=document)

    def list(self, **filters: Any) -> QuerySet[ConversationModel]:
        queryset = ConversationModel.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.order_by("-conversations_created_at")

    @transaction.atomic
    def update(self, model_id: Any, **fields: Any) -> ConversationModel:
        conversation = self.get_by_id(model_id)

        for field_name, value in fields.items():
            setattr(conversation, field_name, value)

        conversation.save(update_fields=list(fields.keys()))
        return conversation

    def update_title(
        self, conversations_id: Any, conversations_title: str
    ) -> ConversationModel:
        return self.update(
            conversations_id,
            conversations_title=conversations_title,
        )

    @transaction.atomic
    def delete(self, model_id: Any) -> int:
        deleted_count, _ = ConversationModel.objects.filter(pk=model_id).delete()
        return deleted_count
