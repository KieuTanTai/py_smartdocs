"""
Message Application Layer.
Handles message-related business logic, validation, and orchestration.
"""

from typing import Optional, Dict, List, Any
from uuid import UUID
import logging

from backend.apps.services.chat.models import ConversationModel, MessageModel
from backend.apps.core.enums.e_provider_name import EProviderName

logger = logging.getLogger(__name__)


class MessageApplication:
    """
    Application layer for message/chat management.
    Handles business logic, validation, and coordination with job manager.
    """

    def __init__(self):
        """Initialize message application."""
        self.logger = logger

    def send_message(
        self,
        conversation_id: UUID,
        user_input: str,
        provider_name: str,
        model_name: str,
        message_type: str = "normal",
    ) -> Dict[str, Any]:
        """
        Process incoming message and prepare for job scheduling.

        Args:
            conversation_id: UUID of conversation
            user_input: User's message text
            provider_name: LLM provider (e.g., 'gemini')
            model_name: Model name
            message_type: Type of chat ('normal', 'cli')

        Returns:
            Dictionary with message request data for job manager

        Raises:
            ValueError: If validation fails
        """
        try:
            # Layer 2 Validation
            self._validate_message_input(
                conversation_id, user_input, provider_name, model_name
            )

            # Check conversation exists
            conversation = ConversationModel.objects.get(pk=conversation_id)

            # Save user message to database
            user_message = MessageModel.objects.create(
                message_conversation_id=conversation_id,
                message_is_user_send=True,
                message_content=user_input,
            )

            self.logger.info(
                f"Created user message {user_message.message_id} in conversation {conversation_id}"
            )

            # Prepare data for job manager
            message_request = {
                "conversation_id": str(conversation_id),
                "user_message_id": str(user_message.message_id),
                "user_input": user_input,
                "provider": provider_name,
                "model": model_name,
                "message_type": message_type,
                "conversation_title": conversation.conversation_title,
            }

            return message_request

        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            raise

    def get_conversation_messages(
        self, conversation_id: UUID, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieve conversation message history.

        Args:
            conversation_id: UUID of conversation
            limit: Maximum number of messages to return
            offset: Offset for pagination

        Returns:
            Dictionary with messages and metadata

        Raises:
            ValueError: If conversation not found
        """
        try:
            # Validate conversation exists
            conversation = ConversationModel.objects.get(pk=conversation_id)

            # Get messages
            messages_qs = MessageModel.objects.filter(
                message_conversation_id=conversation_id
            ).order_by("-message_created_at")[offset : offset + limit]

            messages = [self._serialize_message(m) for m in reversed(messages_qs)]

            return {
                "conversation_id": str(conversation_id),
                "conversation_title": conversation.conversation_title,
                "messages": messages,
                "count": len(messages),
                "total": MessageModel.objects.filter(
                    message_conversation_id=conversation_id
                ).count(),
            }

        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except Exception as e:
            self.logger.error(f"Error retrieving messages: {e}")
            raise

    def save_assistant_response(
        self,
        user_message_id: UUID,
        conversation_id: UUID,
        response_content: str,
        retrieval_time: float = 0.0,
        generation_time: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Save assistant response to database.

        Args:
            user_message_id: UUID of user message
            conversation_id: UUID of conversation
            response_content: Assistant's response text
            retrieval_time: Time spent on retrieval (seconds)
            generation_time: Time spent on generation (seconds)

        Returns:
            Dictionary with assistant message data

        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate user message exists
            user_message = MessageModel.objects.get(pk=user_message_id)

            # Validate conversation matches
            if str(user_message.message_conversation_id) != str(conversation_id):
                raise ValueError(
                    f"User message {user_message_id} does not belong to conversation {conversation_id}"
                )

            # Create assistant message
            assistant_message = MessageModel.objects.create(
                message_conversation_id=conversation_id,
                message_is_user_send=False,
                message_content=response_content,
            )

            self.logger.info(
                f"Created assistant message {assistant_message.message_id} "
                f"(retrieval: {retrieval_time:.2f}s, generation: {generation_time:.2f}s)"
            )

            return self._serialize_message(assistant_message, retrieval_time, generation_time)

        except MessageModel.DoesNotExist:
            raise ValueError(f"User message {user_message_id} not found")
        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error saving assistant response: {e}")
            raise

    def delete_message(self, message_id: UUID) -> None:
        """
        Delete a message.

        Args:
            message_id: UUID of message to delete

        Raises:
            ValueError: If message not found
        """
        try:
            message = MessageModel.objects.get(pk=message_id)
            message.delete()
            self.logger.info(f"Deleted message {message_id}")

        except MessageModel.DoesNotExist:
            raise ValueError(f"Message {message_id} not found")
        except Exception as e:
            self.logger.error(f"Error deleting message: {e}")
            raise

    # ==================== Private Helper Methods ====================

    def _validate_message_input(
        self,
        conversation_id: UUID,
        user_input: str,
        provider_name: str,
        model_name: str,
    ) -> None:
        """
        Validate message input (Layer 2 validation).

        Args:
            conversation_id: UUID of conversation
            user_input: User message text
            provider_name: Provider name
            model_name: Model name

        Raises:
            ValueError: If any validation fails
        """
        if not conversation_id:
            raise ValueError("Conversation ID is required")

        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError("User input must be a non-empty string")

        if not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError("Provider name is required")

        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("Model name is required")

        # Validate input length
        max_length = 10000
        if len(user_input) > max_length:
            raise ValueError(f"User input exceeds maximum length of {max_length}")

    def _serialize_message(
        self,
        message: MessageModel,
        retrieval_time: float = 0.0,
        generation_time: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Serialize message model to dictionary.

        Args:
            message: MessageModel instance
            retrieval_time: Retrieval time (for assistant messages)
            generation_time: Generation time (for assistant messages)

        Returns:
            Dictionary representation
        """
        result = {
            "id": str(message.message_id),
            "conversation_id": str(message.message_conversation_id),
            "role": "user" if message.message_is_user_send else "assistant",
            "content": message.message_content,
            "created_at": message.message_created_at.isoformat(),
        }

        # Add timing information for assistant messages
        if not message.message_is_user_send and (retrieval_time > 0 or generation_time > 0):
            result["metrics"] = {
                "retrieval_time": retrieval_time,
                "generation_time": generation_time,
                "total_time": retrieval_time + generation_time,
            }

        return result
