from abc import ABC, abstractmethod

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.request.i_create_conversation_request import ICreateConversationRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationGetResponse, IConversationPostResponse, IconversationDocumentGetResponse

class IDocumentApplication(ABC):
    @abstractmethod
    def upload_document(self, request: ICreateConversationRequest) -> IConversationPostResponse:
        """
        Uploads a document to the system.
        using process pool executor for upload files, embedding and indexing, this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
        Args:
            request (ICreateConversationRequest): The request object containing document upload details.
        Returns:
            IConversationPostResponse: A response object containing the result of the upload operation.
        """
        pass

    @abstractmethod
    def get_document(self, conversation_id: str) -> IconversationDocumentGetResponse:
        """
        Retrieves a document from the system. this require conversation_id
        this method will use this id for get documents of this conversation
        using thread pool executor for get document, this will help to reduce the time of get document, and also can handle multiple get document at the same time
        Args:
            conversation_id: The unique identifier of the conversation to retrieve.
        Returns:
            IconversationDocumentGetResponse: A response object containing the retrieved document details.
        """
        pass