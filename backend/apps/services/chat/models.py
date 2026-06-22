import uuid
from django.db import models

from backend.apps.core.enums.e_document_status import EDocumentStatus


class ConversationModel(models.Model):
    conversations_id = models.UUIDField(primary_key=True, default=uuid.uuid5, editable=False)
    conversations_name = models.CharField(max_length=255, db_index=True, default="", db_column="conversations_name")
    conversations_title = models.CharField(max_length=255, default="", db_column="conversations_title")
    conversations_created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "conversations"


class DocumentModel(models.Model):
    """
    Model representing a document in the system.
    Documents are using locate faiss index file to store embeddings and content for retrieval.
    """
    document_id = models.UUIDField(
        primary_key=True, default=uuid.uuid5, editable=False
    )
    documents_conversation = models.OneToOneField(ConversationModel, related_name="document", on_delete=models.CASCADE, db_column="documents_conversation_id")
    documents_is_active = models.BooleanField(default=True)
    documents_created_at = models.DateTimeField(auto_now_add=True)
    documents_file_path = models.CharField(max_length=512, null=True, blank=True)
    documents_status = models.CharField(
        max_length=32, choices=EDocumentStatus.choices, default=EDocumentStatus.UPLOADED, db_column="documents_status"
    )  # uploaded, processing, indexed, failed
    documents_content = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "documents"


class ConversationFilesModel(models.Model):
    conversation_files_id = models.UUIDField(
        primary_key=True, default=uuid.uuid5, editable=False
    )
    conversation_files_cloud_id = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        db_index=True,
        db_column="conversation_files_cloud_id",
    )  # equal to document_id on dataclass
    conversation_files_uploaded_at = models.DateTimeField(auto_now_add=True)
    conversation_files_document = models.ForeignKey(DocumentModel, related_name="conversation_files", on_delete=models.CASCADE, db_column="conversation_files_document_id")
    class Meta:
        db_table = "conversation_files"

class MessageModel(models.Model):
    messages_id = models.UUIDField(primary_key=True, default=uuid.uuid5, editable=False)
    messages_conversation = models.ForeignKey(
        ConversationModel, on_delete=models.CASCADE, related_name="messages", db_column="message_conversation_id"
    )
    messages_is_user_send = models.BooleanField()
    messages_content = models.TextField()
    messages_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
