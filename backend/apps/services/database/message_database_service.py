"""
Message database service.
Concrete CRUD implementation for MessageModel.
"""

from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from backend.apps.core.interfaces.services.rag_base.database.i_message_database import (
    IMessageDatabase,
)
from backend.apps.services.chat.models import ConversationModel, MessageModel


class MessageDatabaseService(IMessageDatabase):
    """Django ORM implementation for message CRUD operations."""

    def create(self, **fields: Any) -> MessageModel:
        return MessageModel.objects.create(**fields)

    def create_message(
        self,
        conversation: ConversationModel,
        content: str,
        is_user_send: bool,
        **extra_fields: Any,
    ) -> MessageModel:
        return self.create(
            messages_conversation=conversation,
            messages_content=content,
            messages_is_user_send=is_user_send,
            **extra_fields,
        )

    def get_by_id(self, model_id: Any) -> MessageModel:
        return MessageModel.objects.get(pk=model_id)

    def get_by_ids(self, model_ids: list[Any]) -> QuerySet[MessageModel]:
        return MessageModel.objects.filter(pk__in=model_ids)

    def get_by_conversation(
        self, conversation: ConversationModel
    ) -> QuerySet[MessageModel]:
        return MessageModel.objects.filter(
            messages_conversation=conversation
        ).order_by("messages_created_at")

    def get_user_messages(
        self, conversation: ConversationModel
    ) -> QuerySet[MessageModel]:
        return self.get_by_conversation(conversation).filter(messages_is_user_send=True)

    def get_assistant_messages(
        self, conversation: ConversationModel
    ) -> QuerySet[MessageModel]:
        return self.get_by_conversation(conversation).filter(messages_is_user_send=False)

    def list(self, **filters: Any) -> QuerySet[MessageModel]:
        queryset = MessageModel.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        return queryset.order_by("-messages_created_at")

    @transaction.atomic
    def update(self, model_id: Any, **fields: Any) -> MessageModel:
        message = self.get_by_id(model_id)

        for field_name, value in fields.items():
            setattr(message, field_name, value)

        message.save(update_fields=list(fields.keys()))
        return message

    @transaction.atomic
    def delete(self, model_id: Any) -> int:
        deleted_count, _ = MessageModel.objects.filter(pk=model_id).delete()
        return deleted_count

    @transaction.atomic
    def delete_by_conversation(self, conversation: ConversationModel) -> int:
        deleted_count, _ = MessageModel.objects.filter(
            messages_conversation=conversation
        ).delete()
        return deleted_count
