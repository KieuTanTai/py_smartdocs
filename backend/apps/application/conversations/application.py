"""
Conversation Application Layer.
Handles conversation-related business logic, validation, and orchestration.
"""

from typing import Optional, Dict, List, Any
from uuid import UUID
import logging

from backend.apps.services.chat.models import ConversationModel, DocumentModel, ConversationFilesModel, MessageModel
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionInfo
from backend.apps.core.enums.e_provider_name import EProviderName

logger = logging.getLogger(__name__)


class ConversationApplication:
    """
    Application layer for conversation management.
    Handles business logic, validation, and coordination with job manager.
    """

    def __init__(self):
        """Initialize conversation application."""
        self.logger = logger

    def create_conversation(
        self,
        title: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new conversation with optional documents.

        Args:
            title: Conversation title
            provider_name: LLM provider (e.g., 'gemini', 'mistral')
            model_name: Model name
            system_prompt: Custom system instruction
            document_ids: List of document UUIDs to attach

        Returns:
            Dictionary with conversation data

        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate input
            if not title or not isinstance(title, str):
                raise ValueError("Title must be a non-empty string")

            # Create conversation record
            conversation = ConversationModel.objects.create(
                conversation_title=title
            )
            self.logger.info(
                f"Created conversation {conversation.conversation_id} with title '{title}'"
            )

            # Attach documents if provided
            if document_ids:
                self._attach_documents_to_conversation(
                    conversation.conversation_id, document_ids
                )

            return self._serialize_conversation(conversation)

        except ValueError as e:
            self.logger.error(f"Validation error creating conversation: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating conversation: {e}")
            raise

    def get_conversation(self, conversation_id: UUID) -> Dict[str, Any]:
        """
        Get conversation details.

        Args:
            conversation_id: UUID of conversation

        Returns:
            Dictionary with conversation data

        Raises:
            ValueError: If conversation not found
        """
        try:
            conversation = ConversationModel.objects.get(pk=conversation_id)
            return self._serialize_conversation(conversation)
        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except Exception as e:
            self.logger.error(f"Error retrieving conversation: {e}")
            raise

    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversations.

        Returns:
            List of conversation dictionaries
        """
        try:
            conversations = ConversationModel.objects.all().order_by(
                "-conversation_created_at"
            )
            return [self._serialize_conversation(c) for c in conversations]
        except Exception as e:
            self.logger.error(f"Error listing conversations: {e}")
            raise

    def add_documents_to_conversation(
        self, conversation_id: UUID, document_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Add documents to an existing conversation.

        Args:
            conversation_id: UUID of conversation
            document_ids: List of document UUIDs

        Returns:
            Updated conversation dictionary

        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate conversation exists
            conversation = ConversationModel.objects.get(pk=conversation_id)

            # Validate and attach documents
            self._attach_documents_to_conversation(conversation_id, document_ids)

            return self._serialize_conversation(conversation)

        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")
            raise

    def remove_documents_from_conversation(
        self, conversation_id: UUID, document_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Remove documents from conversation.

        Args:
            conversation_id: UUID of conversation
            document_ids: List of document UUIDs to remove

        Returns:
            Updated conversation dictionary
        """
        try:
            conversation = ConversationModel.objects.get(pk=conversation_id)

            # Delete conversation-file relationships
            ConversationFilesModel.objects.filter(
                conversation=conversation,
                faiss_index_id__in=document_ids
            ).delete()

            self.logger.info(
                f"Removed {len(document_ids)} documents from conversation {conversation_id}"
            )

            return self._serialize_conversation(conversation)

        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except Exception as e:
            self.logger.error(f"Error removing documents: {e}")
            raise

    def delete_conversation(self, conversation_id: UUID) -> None:
        """
        Delete conversation (use transactional handler for full cleanup).

        Args:
            conversation_id: UUID of conversation

        Raises:
            ValueError: If conversation not found
        """
        try:
            conversation = ConversationModel.objects.get(pk=conversation_id)
            conversation.delete()
            self.logger.info(f"Deleted conversation {conversation_id}")

        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except Exception as e:
            self.logger.error(f"Error deleting conversation: {e}")
            raise

    def get_conversation_documents(self, conversation_id: UUID) -> List[Dict[str, Any]]:
        """
        Get documents attached to conversation.

        Args:
            conversation_id: UUID of conversation

        Returns:
            List of document dictionaries
        """
        try:
            conversation = ConversationModel.objects.get(pk=conversation_id)
            
            conversation_files = ConversationFilesModel.objects.filter(
                conversation=conversation
            )

            documents = []
            for cf in conversation_files:
                doc = cf.faiss_index
                documents.append({
                    "id": str(doc.faiss_index_id),
                    "title": doc.faiss_index_file_name,
                    "status": doc.status,
                    "created_at": doc.faiss_index_created_at.isoformat(),
                })

            return documents

        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except Exception as e:
            self.logger.error(f"Error retrieving conversation documents: {e}")
            raise

    # ==================== Private Helper Methods ====================

    def _attach_documents_to_conversation(
        self, conversation_id: UUID, document_ids: List[UUID]
    ) -> None:
        """
        Attach documents to conversation (internal helper).

        Args:
            conversation_id: UUID of conversation
            document_ids: List of document UUIDs
        """
        for doc_id in document_ids:
            try:
                document = DocumentModel.objects.get(pk=doc_id)
                
                # Avoid duplicates
                existing = ConversationFilesModel.objects.filter(
                    conversation_id=conversation_id,
                    faiss_index_id=doc_id
                ).exists()

                if not existing:
                    ConversationFilesModel.objects.create(
                        conversation_id=conversation_id,
                        faiss_index_id=doc_id
                    )
                    self.logger.debug(
                        f"Attached document {doc_id} to conversation {conversation_id}"
                    )

            except DocumentModel.DoesNotExist:
                self.logger.warning(f"Document {doc_id} not found, skipping")
                continue

    def _serialize_conversation(self, conversation: ConversationModel) -> Dict[str, Any]:
        """
        Serialize conversation model to dictionary.

        Args:
            conversation: ConversationModel instance

        Returns:
            Dictionary representation
        """
        return {
            "id": str(conversation.conversation_id),
            "title": conversation.conversation_title,
            "created_at": conversation.conversation_created_at.isoformat(),
            "status": "ready",  # TODO: Add status to model
        }
