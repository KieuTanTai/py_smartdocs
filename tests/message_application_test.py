import sys
import logging
from pathlib import Path
from unittest.mock import MagicMock

# Nếu MessageApplication vẫn import Django models
sys.modules["backend.apps.services.chat.models"] = MagicMock()

from backend.apps.application.messages.application import MessageApplication
from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.application.i_message_response import (
    ISendMessageResponse,
    IChatHistoryResponse,
    IMessageDTO,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

# =====================================================
# Setup
# =====================================================
mock_logger = MagicMock()
mock_task = MagicMock()

app = MessageApplication(
    message_task=mock_task,
    logger=mock_logger,
)


# =====================================================
# SEND MESSAGE TEST
# =====================================================
def test_send_message():
    logger.info("========== TEST SEND MESSAGE ==========")

    mock_task.run.return_value = ISendMessageResponse(
        conversation_id="conv-123",
        user_message_id="msg-user-1",
        assistant_message_id="msg-ai-1",
        assistant_message="Chào bạn, tôi là AI",
        latency_ms=1200,
        provider="gemini",
        model="gemini-1.5-flash",
        pipeline_type=EPipelineType.HYBRID,
    )

    try:
        response = app.send_message(
            conversation_id="conv-123",
            user_input="Hello AI",
            provider_name=EProviderName.GEMINI.value,
            model_name="gemini-1.5-flash",
            pipeline_type=EPipelineType.HYBRID,
        )

        logger.info(
            f"Assistant response: {response.assistant_message}"
        )

        mock_task.run.assert_called_once_with(
            conversation_id="conv-123",
            content="Hello AI",
            provider_name=EProviderName.GEMINI,
            pipeline_type=EPipelineType.HYBRID,
            model_name="gemini-1.5-flash",
        )

        logger.info("TEST SEND MESSAGE: SUCCESS")

    except Exception as e:
        logger.exception(f"TEST SEND MESSAGE FAILED: {e}")


# =====================================================
# GET HISTORY TEST
# =====================================================
def test_get_history():
    logger.info("========== TEST GET HISTORY ==========")

    mock_task.get_history.return_value = IChatHistoryResponse(
        conversation_id="conv-123",
        conversation_title="Báo cáo mật",
        messages=[
            IMessageDTO(
                id="1",
                conversation_id="conv-123",
                role="user",
                content="Hello",
                created_at="2024-01-01T10:00:00Z",
            ),
            IMessageDTO(
                id="2",
                conversation_id="conv-123",
                role="assistant",
                content="Hi there",
                created_at="2024-01-01T10:00:05Z",
            ),
        ],
        count=2,
        total=2,
    )

    try:
        response = app.get_conversation_messages(
            conversation_id="conv-123",
            limit=10,
            offset=0,
        )

        logger.info(
            f"Conversation: {response.conversation_title}"
        )
        logger.info(
            f"Total messages: {response.total}"
        )

        mock_task.get_history.assert_called_once_with(
            conversation_id="conv-123",
            limit=10,
            offset=0,
        )

        logger.info("TEST GET HISTORY: SUCCESS")

    except Exception as e:
        logger.exception(f"TEST GET HISTORY FAILED: {e}")


# =====================================================
# VALIDATION TEST
# =====================================================
def test_validation():
    logger.info("========== TEST VALIDATION ==========")

    try:
        app.send_message(
            conversation_id="",
            user_input="Hello",
            provider_name="gemini",
            model_name="gemini-1.5",
            pipeline_type=EPipelineType.HYBRID,
        )

        logger.error(
            "Validation failed. Empty conversation_id passed."
        )

    except ValueError as e:
        logger.info(
            f"Validation works correctly: {e}"
        )

    except Exception as e:
        logger.exception(
            f"Unexpected error during validation test: {e}"
        )


if __name__ == "__main__":
    test_send_message()

    # reset mock call count
    mock_task.reset_mock()

    test_get_history()
    test_validation()

    logger.info("========== ALL TESTS FINISHED ==========")