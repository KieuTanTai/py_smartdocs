from abc import abstractmethod

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.interfaces.dataclass.application.i_message_response import IChatHistoryResponse, ISendMessageResponse


class IMessageApllication:
    @abstractmethod
    def send_message(
        self,
        conversation_id: str,
        user_input: str,
        provider_name: str,
        model_name: str,
        embedding_model_name: str,
        pipeline_type: EPipelineType, # Thêm loại pipeline để gọi xuống Task
        file_caller: str = ""
    ) -> ISendMessageResponse:
        """
        Quy trình xử lý:
        1. Validate đầu vào.
        2. Lưu tin nhắn User -> DB (Trả ngay cho UI nếu là Async).
        3. Gọi MessageTask xử lý AI (RAG -> Prompt -> LLM -> Lưu DB tin nhắn AI).
        4. Trả về kết quả tổng hợp.
        """
        pass

    @abstractmethod
    def get_conversation_messages(self, conversation_id: str, limit: int = 50, offset: int = 0, file_caller: str = "") -> IChatHistoryResponse:
        """
        Lấy thông tin tin nhắn theo ID.
        """
        pass
