from pathlib import Path
from typing import cast

from backend.apps.core.interfaces.dataclass.request.i_create_conversation_request import ICreateConversationRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationGetResponse, IConversationInfoResponse, IConversationPostResponse, IconversationDocumentGetResponse
from backend.apps.core.interfaces.dataclass.tasks.i_upload_response import IUploadResponse
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.system.i_time_counter import ITimeCounter
from backend.apps.interfaces.application.document.i_document_application import IDocumentApplication
from backend.apps.interfaces.tasks.i_upload_task import IUploadTask
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from backend.apps.services.chat.models import ConversationFilesModel, DocumentModel

class DocumentApplication(IDocumentApplication):

    def __init__(
        self,
        upload_task: IUploadTask,
        logger: ILogger,
    ):
        self.upload_task = upload_task
        self.logger = logger

    def upload_document(self, request: ICreateConversationRequest, file_caller: str = "") -> IConversationPostResponse:
        self.logger.info(f"Starting document upload for conversation_id: {request.conversation_id}",
                         Path(__file__).name, file_caller, self.upload_document.__name__)
        return self.__upload_document_task(request, file_caller)

    def list_files(self, conversation_id: str, file_caller: str = "") -> list[ConversationFilesModel]:
        self.logger.info(f"Listing files for conversation_id: {conversation_id}",
                         Path(__file__).name, file_caller, self.list_files.__name__)
        try:
            response = self.upload_task.list_files(conversation_id, file_caller)
            return response
        except Exception as e:
            self.logger.error(f"Error listing files for conversation_id: {conversation_id}, error: {str(e)}",
                              Path(__file__).name, file_caller, self.list_files.__name__)
            raise e

    def __upload_document_task(self, request: ICreateConversationRequest, file_caller: str = "") -> IConversationPostResponse:
        response = self.__run_upload_task(request, file_caller)
        title = response.summarize.content[:50] if response.summarize else None
        self.logger.info(f"Upload document task completed for conversation_id: {request.conversation_id}, provider: {request.provider}, model_name: {request.model_name}",
                         Path(__file__).name, file_caller, self.__upload_document_task.__name__)
        metadata = IConversationInfoResponse(
            conversation_name=response.conversation_name,
            provider=request.provider,
            model_name=request.model_name,
            conversation_title=title if title else "",
            document_urls=request.document_urls,
            document_paths=request.document_paths,
            type=request.type,
            create_at=response.created_at
        )
        self.logger.info(f"Document metadata created for conversation_id: {request.conversation_id}",
                         Path(__file__).name, file_caller, self.__upload_document_task.__name__ )
        #! NOTE: time_counter is not implemented yet, so the time_counter in response is None,
        #! this will be implemented in the future
        return IConversationPostResponse(
            index=response.faiss_index,
            info=metadata,
            time_counter= response.time_counter if response.time_counter else None
        )
    
    def __run_upload_task(self, request: ICreateConversationRequest, file_caller: str = "") -> IUploadResponse:
        self.logger.info(f"Running upload task for conversation_id: {request.conversation_id}",
                         Path(__file__).name, file_caller, self.__run_upload_task.__name__)
        try:
            paths = request.document_paths if request.document_paths else []
            provider = request.provider
            response = self.upload_task.run_with_paths(request.conversation_id, paths, provider, request.model_name)
            return response
        except ValueError as ve:
            self.logger.error(f"ValueError running upload task for conversation_id: {request.conversation_id}, error: {str(ve)}",
                              Path(__file__).name, file_caller, self.__run_upload_task.__name__)
            raise ve

        except Exception as e:
            self.logger.error(f"Error running upload task for conversation_id: {request.conversation_id}, error: {str(e)}",
                              Path(__file__).name, file_caller, self.__run_upload_task.__name__)
            raise e