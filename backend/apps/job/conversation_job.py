import uuid

# Import Interfaces
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, MessageModel

class ConversationJob(IConversationJob):

    def __init__(self, llm_provider_factory: ILLMProviderFactory, llm_prompt_structure: ILLMPromptStructure, config_provider: IConfigProvider, logger: ILogger, hybrid_search_service: IHybridSearchService | None = None):
        self.llm_provider_factory = llm_provider_factory
        self.llm_prompt_structure = llm_prompt_structure
        self.config_provider = config_provider
        self.logger = logger
        self.hybrid_search_service = hybrid_search_service

    def check_documents_ready(self, conversation_id: str | uuid.UUID) -> bool:
        try:
            if isinstance(conversation_id, uuid.UUID):
                conversation = ConversationModel.objects.get(pk=conversation_id)
            else:
                conversation = ConversationModel.objects.get(conversation_id=conversation_id)
                
            faiss_index = conversation.conversation_faiss_index
            documents = ConversationFilesModel.objects.filter(conversation=conversation)
            
            if not faiss_index or not faiss_index.faiss_index_is_active:
                return False
            if not documents.exists():
                self.logger.warning(f"No documents attached to conversation {conversation_id}.", source=__file__, call_by=self.check_documents_ready.__name__)
                return False 
            return True
        except ConversationModel.DoesNotExist:
            self.logger.error(f"Conversation not found: {conversation_id}", source=__file__, call_by=self.check_documents_ready.__name__)
            raise ValueError(f"Conversation not found: {conversation_id}")

    def generate_bootstrap_message(self, conversation_id: str, provider: EProviderName, model_name: str | None = None) -> IConversationJobResponse:
        try:
            conversation = ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation not found: {conversation_id}")

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

    def _generate_assistant_response(self, prompt: str, provider: EProviderName, model_name: str) -> str:
        llm_client = self.llm_provider_factory.get_provider(provider)
        response = llm_client.generate(ICompletionRequest(provider=provider, model=model_name, prompt=prompt, context_hits=[]))
        return response.message_content if hasattr(response, 'message_content') else response

    def _save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        return MessageModel.objects.create(message_conversation=conversation, message_is_user_send=is_user_send, message_content=content)