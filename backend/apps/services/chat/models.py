import uuid
from django.db import models

from backend.apps.core.enums.e_document_status import EDocumentStatus


class ConversationModel(models.Model):
    conversations_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
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
        primary_key=True, default=uuid.uuid7, editable=False
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

class ConversationCacheModel(models.Model):
    """
    Model representing metadata for conversation cache.(this model is the same to DocumentModel but for cache data, not the metadata of document)
     - conversation_cache_id: Unique identifier for the cache metadata.
     - conversation_cache_conversation: One-to-one relationship with the ConversationModel, linking the cache metadata to a specific conversation.
     - conversation_cache_is_active: Boolean field indicating whether the cache metadata is active or not.
     - conversation_cache_file_path: CharField to store the file path of the cached data, allowing for efficient retrieval of cached content.
     - conversation_cache_created_at: DateTimeField to track when the cache metadata was created, useful for cache management and expiration strategies.
     - conversation_cache_status: UUIDField to store the status of the cache metadata, which can be used to track the state of the cache (e.g., valid, expired, or in the process of being updated).
    """
    conversation_cache_id = models.UUIDField(
        primary_key=True, default=uuid.uuid7, editable=False
    )
    conversation_cache_conversation = models.OneToOneField(ConversationModel, related_name="conversation_cache", on_delete=models.CASCADE, db_column="conversation_cache_conversation_id")
    conversation_cache_is_active = models.BooleanField(default=True)
    conversation_cache_file_path = models.CharField(max_length=512, null=True, blank=True)
    conversation_cache_created_at = models.DateTimeField(auto_now=True)
    conversation_cache_status = models.CharField(
        max_length=32, choices=EDocumentStatus.choices, default=EDocumentStatus.UPLOADED, db_column="conversation_status"
    ) 
    class Meta:
        db_table = "conversation_cache"

class ConversationFilesModel(models.Model):
    conversation_files_id = models.UUIDField(
        primary_key=True, default=uuid.uuid7, editable=False
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
    messages_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    messages_conversation = models.ForeignKey(
        ConversationModel, on_delete=models.CASCADE, related_name="messages", db_column="message_conversation_id"
    )
    messages_is_user_send = models.BooleanField()
    messages_content = models.TextField()
    messages_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
