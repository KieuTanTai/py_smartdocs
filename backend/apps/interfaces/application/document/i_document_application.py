from abc import ABC, abstractmethod

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.request.i_create_conversation_request import ICreateConversationRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationGetResponse, IConversationPostResponse, IconversationDocumentGetResponse
from backend.apps.services.chat.models import ConversationFilesModel

class IDocumentApplication(ABC):
    @abstractmethod
    def upload_document(self, request: ICreateConversationRequest, file_caller: str = "") -> IConversationPostResponse:
        """
        Uploads a document to the system.
        using process pool executor for upload files, embedding and indexing, this will help to reduce the time of upload document, and also can handle multiple upload document at the same time
        Args:
            request (ICreateConversationRequest): The request object containing document upload details.
            file_caller (str): The caller of the file upload operation.
        Returns:
            IConversationPostResponse: A response object containing the result of the upload operation.
        """
        pass

    @abstractmethod
    def list_files(self, conversation_id: str, file_caller: str = "") -> list[ConversationFilesModel]:
        """
        Lists all files associated with a specific conversation.
        Args:
            conversation_id (str): The ID of the conversation for which to list files.
            file_caller (str): The caller of the file listing operation.
        Returns:
            list[ConversationFilesModel]: A list of ConversationFilesModel objects representing the files in the conversation.
        """
        pass