from backend.apps.core.interfaces.dataclass.request.i_create_conversation_request import ICreateConversationRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationGetResponse, IConversationPostResponse
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.system.i_time_counter import ITimeCounter
from backend.apps.interfaces.application.document.i_document_application import IDocumentApplication
from backend.apps.interfaces.tasks.i_upload_task import IUploadTask


class DocumentApplication(IDocumentApplication):

    def __init__(
        self,
        upload_task: IUploadTask,
        cache_session: IConnectCacheSession,
        logger: ILogger,
        time_counter: ITimeCounter,
    ):
        self.upload_task = upload_task
        self.cache_session = cache_session
        self.logger = logger
        self.time_counter = time_counter

    def upload_document(self, request: ICreateConversationRequest) -> IConversationPostResponse:
        pass

    def get_document(self, document_id) -> IConversationGetResponse:
        pass
