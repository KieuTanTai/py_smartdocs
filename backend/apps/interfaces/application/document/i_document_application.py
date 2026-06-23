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
