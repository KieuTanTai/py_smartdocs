from abc import ABC, abstractmethod
from typing import List

from backend.apps.core.interfaces.dataclass.request.i_run_application_request import (
    IDeleteConversationApplicationRequest,
    ISendMessageApplicationRequest,
    IUploadApplicationRequest,
)
from backend.apps.core.interfaces.dataclass.response.i_run_application_response import (
    IGetConversationApplicationResponse,
    ISendMessageApplicationResponse,
    IUploadApplicationResponse,
)


class IRunApplication(ABC):
    """Interface cho application layer tổng hợp.
    Quản lý toàn bộ nghiệp vụ: upload, send message, get/delete conversation.
    Tất cả dependency được inject qua constructor (IoC/DI).
    """

    @abstractmethod
    def upload(self, request: IUploadApplicationRequest) -> IUploadApplicationResponse:
        """Upload tài liệu, tạo conversation, chạy pipeline xử lý.
        Flow: tạo conversation → extract → normalize → chunk → embed → save → summarize.
        Args:
            request: IUploadApplicationRequest chứa provider, model_name, document_paths/urls, type.
        Returns:
            IUploadApplicationResponse chứa id, title, status, conversation_id, date_create.
        """
        pass

    @abstractmethod
    def send_message(self, request: ISendMessageApplicationRequest) -> ISendMessageApplicationResponse:
        """Gửi tin nhắn chat vào conversation, thực hiện RAG retrieval + LLM generate.
        Args:
            request: ISendMessageApplicationRequest chứa conversation_id, message, provider, model_name, type.
        Returns:
            ISendMessageApplicationResponse chứa message, used_mock, conversation_id.
        """
        pass

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> IGetConversationApplicationResponse:
        """Lấy thông tin conversation.
        Args:
            conversation_id: UUID của conversation.
        Returns:
            IGetConversationApplicationResponse chứa conversation_id, status, date_create.
        """
        pass

    @abstractmethod
    def list_conversations(self) -> List[IGetConversationApplicationResponse]:
        """Lấy danh sách tất cả conversations.
        Returns:
            List[IGetConversationApplicationResponse].
        """
        pass

    @abstractmethod
    def delete_conversation(self, request: IDeleteConversationApplicationRequest) -> None:
        """Xóa conversation và tất cả dữ liệu liên quan.
        Xóa sạch: messages, files, FAISS index, BM25 index, Redis cache, Neo4j graph data.
        Args:
            request: IDeleteConversationApplicationRequest chứa conversation_id.
        """
        pass
