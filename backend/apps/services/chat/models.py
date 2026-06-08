import uuid
from django.db import models

class ConversationModel(models.Model):
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_title = models.CharField(max_length=255)
    conversation_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversation"

class DocumentModel(models.Model):
    faiss_index_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faiss_index_file_name = models.CharField(max_length=255)
    faiss_index_is_active = models.BooleanField(default=True)
    faiss_index_created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=512, null=True, blank=True)
    status = models.CharField(max_length=32, default="uploaded")  # uploaded, processing, indexed, failed
    content = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "faiss_index"

class ConversationFilesModel(models.Model):
    conversation_files_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faiss_index = models.ForeignKey(DocumentModel, on_delete=models.CASCADE, db_column="faiss_index_id")
    conversation = models.ForeignKey(ConversationModel, on_delete=models.CASCADE, db_column="conversation_files_conversation_id")

    class Meta:
        db_table = "conversation_files"

class MessageModel(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_conversation = models.ForeignKey(ConversationModel, on_delete=models.CASCADE, db_column="message_conversation_id")
    message_is_user_send = models.BooleanField()
    message_content = models.TextField()
    message_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
