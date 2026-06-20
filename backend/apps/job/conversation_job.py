from typing import Any, cast
import uuid

# Import Interfaces
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import IConversationDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, DocumentModel, MessageModel
from backend.apps.utils.get_instance_model_database import get_instance_model_database

class ConversationJob(IConversationJob):

    def __init__(self, llm_provider_factory: ILLMProviderFactory, llm_prompt_structure: ILLMPromptStructure, config_provider: IConfigProvider, 
                 database_provider: IDatabaseProvider,
                 logger: ILogger, hybrid_search_service: IHybridSearchService | None = None):
        self.llm_provider_factory = llm_provider_factory
        self.llm_prompt_structure = llm_prompt_structure
        self.config_provider = config_provider
        self.database_provider = database_provider
        self.logger = logger
        self.hybrid_search_service = hybrid_search_service
        self.document_database: IDocumentDatabase = cast(IDocumentDatabase, self.database_provider.get_model_service(DocumentModel))

    def __ensure_database_initialized(self, database_model: Any) -> None:
        """Ensure that the document database is initialized."""
        if self.document_database is None:
            obj_instance = get_instance_model_database(DocumentModel, self.database_provider)
            if isinstance(obj_instance, IDocumentDatabase):
                self.document_database = obj_instance
            else:
                raise RuntimeError("Document database service is not available.")

    def check_documents_ready(self, conversation_key:uuid.UUID) -> bool:
        try:
            if not self.document_database:
                self.__ensure_database_initialized(DocumentModel)
            existed = self.document_database.get_by_id(conversation_key)
            if not existed or not existed.documents_status.lower().strip() == "indexed":
                return False
            return True
        except Exception as e:
            self.logger.error(
                f"Error checking document readiness for conversation {conversation_key}: {str(e)}",
                source=__file__,
                call_by=ConversationJob.check_documents_ready.__name__,
                method_call=self.check_documents_ready.__name__,
            )
            return False

    def generate_bootstrap_message(self, conversation_key: uuid.UUID, provider: EProviderName, model_name: str | None = None) -> IConversationJobResponse:
        try:
            conversation = ConversationModel.objects.get(pk=conversation_key)
        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation not found: {conversation_key}")

        # TỰ ĐỘNG SINH PROMPT BÊN TRONG JOB
        mappings = ConversationFilesModel.objects.filter(conversation=conversation).select_related('faiss_index')
        file_names = [getattr(m.faiss_index, 'file_name', str(m.faiss_index.faiss_index_id)[:8]) for m in mappings if m.faiss_index]
        
        if file_names:
            file_list_str = ", ".join(file_names)
            prompt = f"Bạn là trợ lý AI thông minh chuyên phân tích tài liệu. Người dùng vừa tải lên các tài liệu: [{file_list_str}]. Hãy gửi một lời chào ngắn gọn báo rằng bạn đã xử lý xong tài liệu."
        else:
            prompt = "Bạn là trợ lý AI thông minh. Hãy gửi lời chào thân thiện đến người dùng."

        model = model_name or "gemini-2.5-flash"
        assistant_message = self._generate_assistant_response(prompt, provider, model)
        self._save_message(conversation, is_user_send=False, content=assistant_message)

        return IConversationJobResponse(
            conversation_id=str(conversation.conversation_id),
            assistant_message=assistant_message,
            provider=provider.value,
            model=model,
        )

    def __generate_assistant_response(self, prompt: str, provider: EProviderName, model_name: str) -> str:
        llm_client = self.llm_provider_factory.get_provider(provider)
        response = llm_client.generate(ICompletionRequest(provider=provider, model=model_name, prompt=prompt, context_hits=[]))
        return response.message_content if hasattr(response, 'message_content') else response

    def __save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        return MessageModel.objects.create(message_conversation=conversation, message_is_user_send=is_user_send, message_content=content)