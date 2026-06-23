import uuid
import os
from django.db import models

from backend.apps.core.enums.e_document_status import EDocumentStatus


class ConversationModel(models.Model):
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, db_column="conversations_id")
    conversation_name = models.CharField(max_length=255, db_index=True, default="", db_column="conversations_name", null=True, blank=True)
    conversation_title = models.CharField(max_length=255, default="", db_column="conversations_title", null=True, blank=True)
    conversation_created_at = models.DateTimeField(auto_now_add=True, db_column="conversations_created_at")

    def __init__(self, *args, **kwargs):
        # Map plural properties if passed as keyword arguments
        if 'conversations_id' in kwargs:
            kwargs['conversation_id'] = kwargs.pop('conversations_id')
        if 'conversations_name' in kwargs:
            kwargs['conversation_name'] = kwargs.pop('conversations_name')
        if 'conversations_title' in kwargs:
            kwargs['conversation_title'] = kwargs.pop('conversations_title')
        if 'conversations_created_at' in kwargs:
            kwargs['conversation_created_at'] = kwargs.pop('conversations_created_at')
            
        # Support other legacy naming
        if 'conversation_id' in kwargs:
            kwargs['conversation_id'] = kwargs.pop('conversation_id')
        if 'conversation_name' in kwargs:
            kwargs['conversation_name'] = kwargs.pop('conversation_name')
        if 'conversation_title' in kwargs:
            kwargs['conversation_title'] = kwargs.pop('conversation_title')
        if 'conversation_created_at' in kwargs:
            kwargs['conversation_created_at'] = kwargs.pop('conversation_created_at')
            
        super().__init__(*args, **kwargs)

    @property
    def conversations_id(self):
        return self.conversation_id
    
    @conversations_id.setter
    def conversations_id(self, value):
        self.conversation_id = value

    @property
    def conversations_name(self):
        return self.conversation_name
    
    @conversations_name.setter
    def conversations_name(self, value):
        self.conversation_name = value

    @property
    def conversations_title(self):
        return self.conversation_title
    
    @conversations_title.setter
    def conversations_title(self, value):
        self.conversation_title = value

    @property
    def conversations_created_at(self):
        return self.conversation_created_at
    
    @conversations_created_at.setter
    def conversations_created_at(self, value):
        self.conversation_created_at = value

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
    conversation = models.ForeignKey(
        ConversationModel, on_delete=models.CASCADE, db_column="documents_conversation_id", null=True, blank=True
    )
    is_active = models.BooleanField(default=True, db_column="documents_is_active")
    created_at = models.DateTimeField(auto_now_add=True, db_column="documents_created_at")
    file_path = models.CharField(max_length=512, null=True, blank=True, db_column="documents_file_path")
    status = models.CharField(
        max_length=32, choices=EDocumentStatus.choices, default=EDocumentStatus.UPLOADED, db_column="documents_status"
    )  # uploaded, processing, indexed, failed
    content = models.TextField(null=True, blank=True, db_column="documents_content")

    def __init__(self, *args, **kwargs):
        # Support plural/prefixed naming in kwargs
        if 'documents_conversation' in kwargs:
            kwargs['conversation'] = kwargs.pop('documents_conversation')
        if 'documents_conversation_id' in kwargs:
            kwargs['conversation_id'] = kwargs.pop('documents_conversation_id')
        if 'documents_is_active' in kwargs:
            kwargs['is_active'] = kwargs.pop('documents_is_active')
        if 'documents_created_at' in kwargs:
            kwargs['created_at'] = kwargs.pop('documents_created_at')
        if 'documents_file_path' in kwargs:
            kwargs['file_path'] = kwargs.pop('documents_file_path')
        if 'documents_status' in kwargs:
            kwargs['status'] = kwargs.pop('documents_status')
        if 'documents_content' in kwargs:
            kwargs['content'] = kwargs.pop('documents_content')

        # Support faiss legacy naming
        if 'faiss_index_id' in kwargs:
            kwargs['document_id'] = kwargs.pop('faiss_index_id')
        if 'faiss_index_file_name' in kwargs:
            file_name = kwargs.pop('faiss_index_file_name')
            if 'file_path' in kwargs:
                kwargs['file_path'] = kwargs.pop('file_path')
            elif file_name and 'file_path' not in kwargs:
                kwargs['file_path'] = file_name
        elif 'file_path' in kwargs:
            kwargs['file_path'] = kwargs.pop('file_path')
            
        if 'faiss_index_is_active' in kwargs:
            kwargs['is_active'] = kwargs.pop('faiss_index_is_active')
        if 'faiss_index_created_at' in kwargs:
            kwargs['created_at'] = kwargs.pop('faiss_index_created_at')
        if 'status' in kwargs:
            kwargs['status'] = kwargs.pop('status')
        if 'content' in kwargs:
            kwargs['content'] = kwargs.pop('content')
            
        super().__init__(*args, **kwargs)

    @property
    def documents_conversation(self):
        return self.conversation

    @documents_conversation.setter
    def documents_conversation(self, value):
        self.conversation = value

    @property
    def documents_conversation_id(self):
        return self.conversation_id

    @documents_conversation_id.setter
    def documents_conversation_id(self, value):
        self.conversation_id = value

    @property
    def documents_is_active(self):
        return self.is_active

    @documents_is_active.setter
    def documents_is_active(self, value):
        self.is_active = value

    @property
    def documents_created_at(self):
        return self.created_at

    @documents_created_at.setter
    def documents_created_at(self, value):
        self.created_at = value

    @property
    def documents_file_path(self):
        return self.file_path

    @documents_file_path.setter
    def documents_file_path(self, value):
        self.file_path = value

    @property
    def documents_status(self):
        return self.status

    @documents_status.setter
    def documents_status(self, value):
        self.status = value

    @property
    def documents_content(self):
        return self.content

    @documents_content.setter
    def documents_content(self, value):
        self.content = value

    # Legacy properties
    @property
    def faiss_index_id(self):
        return self.document_id
    
    @faiss_index_id.setter
    def faiss_index_id(self, value):
        self.document_id = value

    @property
    def faiss_index_file_name(self):
        if self.file_path:
            return os.path.basename(self.file_path)
        return ""
    
    @faiss_index_file_name.setter
    def faiss_index_file_name(self, value):
        pass

    @property
    def faiss_index_is_active(self):
        return self.is_active
    
    @faiss_index_is_active.setter
    def faiss_index_is_active(self, value):
        self.is_active = value

    @property
    def faiss_index_created_at(self):
        return self.created_at
    
    @faiss_index_created_at.setter
    def faiss_index_created_at(self, value):
        self.created_at = value

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
    conversation_cache_status = models.UUIDField(null=True, blank=True)
    class Meta:
        db_table = "conversation_cache"

class ConversationFilesModel(models.Model):
    conversation_files_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    faiss_index = models.ForeignKey(
        DocumentModel, on_delete=models.CASCADE, db_column="conversation_files_cloud_id", null=True, blank=True
    )
    conversation_files_uploaded_at = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(
        ConversationModel, on_delete=models.CASCADE, db_column="conversation_files_conversation_id", null=True, blank=True
    )

    def __init__(self, *args, **kwargs):
        # Support prefixed names in kwargs
        if 'conversation_files_conversation' in kwargs:
            kwargs['conversation'] = kwargs.pop('conversation_files_conversation')
        if 'conversation_files_conversation_id' in kwargs:
            kwargs['conversation_id'] = kwargs.pop('conversation_files_conversation_id')
        if 'conversation_files_cloud_id' in kwargs:
            kwargs['faiss_index_id'] = kwargs.pop('conversation_files_cloud_id')
            
        # Support old kwargs format
        if 'conversation' in kwargs:
            kwargs['conversation'] = kwargs.pop('conversation')
        if 'conversation_id' in kwargs:
            kwargs['conversation_id'] = kwargs.pop('conversation_id')
        if 'faiss_index' in kwargs:
            faiss_index = kwargs.pop('faiss_index')
            if isinstance(faiss_index, DocumentModel):
                kwargs['faiss_index'] = faiss_index
            else:
                kwargs['faiss_index_id'] = str(faiss_index)
        elif 'faiss_index_id' in kwargs:
            kwargs['faiss_index_id'] = str(kwargs.pop('faiss_index_id'))
            
        super().__init__(*args, **kwargs)

    @property
    def conversation_files_conversation(self):
        return self.conversation

    @conversation_files_conversation.setter
    def conversation_files_conversation(self, value):
        self.conversation = value

    @property
    def conversation_files_conversation_id(self):
        return self.conversation_id

    @conversation_files_conversation_id.setter
    def conversation_files_conversation_id(self, value):
        self.conversation_id = value

    @property
    def conversation_files_cloud_id(self):
        return self.faiss_index_id

    @conversation_files_cloud_id.setter
    def conversation_files_cloud_id(self, value):
        self.faiss_index_id = value

    class Meta:
        db_table = "conversation_files"


class MessageModel(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, db_column="messages_id")
    conversation = models.ForeignKey(
        ConversationModel, on_delete=models.CASCADE, related_name="messages", db_column="message_conversation_id", null=True, blank=True
    )
    is_user_send = models.BooleanField(default=False, db_column="messages_is_user_send")
    content = models.TextField(null=True, blank=True, db_column="messages_content")
    created_at = models.DateTimeField(auto_now_add=True, db_column="messages_created_at")

    def __init__(self, *args, **kwargs):
        # Support prefixed names in kwargs
        if 'messages_id' in kwargs:
            kwargs['message_id'] = kwargs.pop('messages_id')
        if 'messages_conversation' in kwargs:
            kwargs['conversation'] = kwargs.pop('messages_conversation')
        if 'messages_conversation_id' in kwargs:
            kwargs['conversation_id'] = kwargs.pop('messages_conversation_id')
        if 'messages_is_user_send' in kwargs:
            kwargs['is_user_send'] = kwargs.pop('messages_is_user_send')
        if 'messages_content' in kwargs:
            kwargs['content'] = kwargs.pop('messages_content')
        if 'messages_created_at' in kwargs:
            kwargs['created_at'] = kwargs.pop('messages_created_at')

        # Support old kwargs format
        if 'message_id' in kwargs:
            kwargs['message_id'] = kwargs.pop('message_id')
        if 'message_conversation' in kwargs:
            kwargs['conversation'] = kwargs.pop('message_conversation')
        if 'message_conversation_id' in kwargs:
            kwargs['conversation_id'] = kwargs.pop('message_conversation_id')
        if 'message_is_user_send' in kwargs:
            kwargs['is_user_send'] = kwargs.pop('message_is_user_send')
        if 'message_content' in kwargs:
            kwargs['content'] = kwargs.pop('message_content')
        if 'message_created_at' in kwargs:
            kwargs['created_at'] = kwargs.pop('message_created_at')
            
        super().__init__(*args, **kwargs)

    @property
    def messages_id(self):
        return self.message_id

    @messages_id.setter
    def messages_id(self, value):
        self.message_id = value

    @property
    def messages_conversation(self):
        return self.conversation

    @messages_conversation.setter
    def messages_conversation(self, value):
        self.conversation = value

    @property
    def messages_conversation_id(self):
        return self.conversation_id

    @messages_conversation_id.setter
    def messages_conversation_id(self, value):
        self.conversation_id = value

    @property
    def messages_is_user_send(self):
        return self.is_user_send

    @messages_is_user_send.setter
    def messages_is_user_send(self, value):
        self.is_user_send = value

    @property
    def messages_content(self):
        return self.content

    @messages_content.setter
    def messages_content(self, value):
        self.content = value

    @property
    def messages_created_at(self):
        return self.created_at

    @messages_created_at.setter
    def messages_created_at(self, value):
        self.created_at = value

    # Legacy attributes
    @property
    def message_conversation_id(self):
        return self.conversation_id

    @message_conversation_id.setter
    def message_conversation_id(self, value):
        self.conversation_id = value

    class Meta:
        db_table = "messages"
