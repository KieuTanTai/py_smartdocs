from typing import cast

from backend.apps.core.interfaces.dataclass.request.i_create_conversation_request import ICreateConversationRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationGetResponse, IConversationInfoResponse, IConversationPostResponse, IconversationDocumentGetResponse
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.system.i_time_counter import ITimeCounter
from backend.apps.interfaces.application.document.i_document_application import IDocumentApplication
from backend.apps.interfaces.tasks.i_upload_task import IUploadTask
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from backend.apps.services.chat.models import DocumentModel

class DocumentApplication(IDocumentApplication):

    def __init__(
        self,
        upload_task: IUploadTask,
        cache_session: IConnectCacheSession,
        database_provider: IDatabaseProvider,
        logger: ILogger,
        time_counter: ITimeCounter,
    ):
        self.upload_task = upload_task
        self.cache_session = cache_session
        self.logger = logger
        self.time_counter = time_counter
        self.database_provider = database_provider
        self.document_database = cast(IDocumentDatabase, self.database_provider.get_model_service(DocumentModel))

    def upload_document(self, request: ICreateConversationRequest) -> IConversationPostResponse:
        return self.__upload_document_task(request)

    def get_document(self, conversation_id: str) -> IconversationDocumentGetResponse:
        return self.upload_task.load_document(conversation_id, file_caller=self.get_document.__name__)

    def __upload_document_task(self, request: ICreateConversationRequest) -> IConversationPostResponse:
        paths = request.document_paths if request.document_paths else []
        provider = request.provider
        response = self.upload_task.run_with_paths(request.conversation_id, paths, provider, request.model_name)
        metadata = IConversationInfoResponse(
            conversation_name=response.conversation_name,
            provider=provider,
            model_name=request.model_name,
            document_urls=request.document_urls,
            document_paths=request.document_paths,
            type=request.type,
            create_at=response.created_at
        )
        #! NOTE: time_counter is not implemented yet, so the time_counter in response is None,
        #! this will be implemented in the future
        return IConversationPostResponse(
            index=response.faiss_index,
            info=metadata,
            time_counter= response.time_counter if response.time_counter else None
        )
