"""
Message Application Layer.
Handles message-related business logic, validation, and orchestration.
"""

from typing import Any, Dict

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.application.i_message_response import IChatHistoryResponse, IMessageDTO, ISendMessageResponse
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.tasks.i_message_task import IMessageTask


class MessageApplication():
    """
    Nhạc trưởng (Orchestrator) quản lý luồng tin nhắn.
    Bơm IMessageTask vào để xử lý RAG & LLM.
    """

    def __init__(self, message_task: IMessageTask, logger: ILogger):
        self.message_task = message_task
        self.logger = logger

    def send_message(
        self,
        conversation_id: str,
        user_input: str,
        provider_name: str,
        model_name: str,
        pipeline_type: EPipelineType, # Thêm loại pipeline để gọi xuống Task
    ) -> ISendMessageResponse:
        try:
            self._validate_message_input(conversation_id, user_input, provider_name, model_name)

            self.logger.info(f"Delegating message to Task for conversation {conversation_id}")
            
            ai_response = self.message_task.run(
                conversation_id=conversation_id,
                content=user_input,
                provider_name=EProviderName(provider_name),
                pipeline_type=EPipelineType(pipeline_type),
                model_name=model_name
            )

            # TRẢ VỀ OBJECT DATACLASS THAY VÌ DICT
            return ISendMessageResponse(
                conversation_id=conversation_id,
                user_message_id=getattr(ai_response, 'user_message_id', ""),
                assistant_message_id=getattr(ai_response, 'assistant_message_id', ""),
                assistant_message=getattr(ai_response, 'assistant_message', ""), 
                latency_ms=getattr(ai_response, 'latency_ms', 0),
                provider=provider_name,
                model=model_name,
                pipeline_type=pipeline_type,
            )

        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            raise

    def get_conversation_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> IChatHistoryResponse:
        try:
            self.logger.info(f"Application routing get_history to Task...")
            
            return self.message_task.get_history(
                conversation_id=conversation_id, 
                limit=limit, 
                offset=offset
            )
        except Exception as e:
            self.logger.error(f"Error: {e}")
            raise

    # ==================== Private Helper Methods ====================

    def _validate_message_input(
        self, conversation_id: str, user_input: str, provider_name: str, model_name: str
    ) -> None:
        if not conversation_id:
            raise ValueError("Conversation ID is required")
        if not isinstance(user_input, str) or not user_input.strip():
            raise ValueError("User input must be a non-empty string")
        if not isinstance(provider_name, str) or not provider_name.strip():
            raise ValueError("Provider name is required")
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("Model name is required")
        if len(user_input) > 10000:
            raise ValueError(f"User input exceeds maximum length of 10000")

