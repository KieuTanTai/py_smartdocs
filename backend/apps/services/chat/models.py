import uuid
from django.db import models

from backend.apps.core.enums.e_document_status import EDocumentStatus


class DocumentModel(models.Model):
    faiss_index_id = models.UUIDField(
        primary_key=True, default=uuid.uuid7, editable=False
    )
    # faiss_index_file_name = models.CharField(max_length=255, db_index=True, db_column="faiss_index_file_name")
    faiss_index_is_active = models.BooleanField(default=True)
    faiss_index_created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=512, null=True, blank=True)
    status = models.CharField(
        max_length=32, choices=EDocumentStatus.choices, default=EDocumentStatus.UPLOADED, db_column="status"
    )  # uploaded, processing, indexed, failed
    content = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "faiss_index"


class ConversationModel(models.Model):
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    conversation_faiss_index = models.ForeignKey(DocumentModel, on_delete=models.CASCADE, null=True, blank=True, db_column="conversation_faiss_index_id")
    conversation_name = models.CharField(max_length=255, db_index=True, db_column="conversation_name")
    conversation_title = models.CharField(max_length=255)
    conversation_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversation"

class ConversationFilesModel(models.Model):
    conversation_files_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    conversation_files_cloud_id = models.CharField(max_length=255, null=False, blank=False, db_index=True, db_column="conversation_files_cloud_id") # equal to document_id on dataclass
    conversation_files_uploaded_at = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(ConversationModel, on_delete=models.CASCADE, db_column="conversation_files_conversation_id")
    class Meta:
        db_table = "conversation_files"

class MessageModel(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    message_conversation = models.ForeignKey(
        ConversationModel, on_delete=models.CASCADE, db_column="message_conversation_id"
    )
    message_is_user_send = models.BooleanField()
    message_content = models.TextField()
    message_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
