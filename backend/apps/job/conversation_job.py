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

    def check_documents_ready(self, conversation_key: str | uuid.UUID) -> bool:
        try:
            conversation = None
            if type(conversation_key) is uuid.UUID:
                conversation = ConversationModel.objects.get(pk=conversation_key)
            else:
                conversation = ConversationModel.objects.get(conversation_name=conversation_key)
            faiss_index = conversation.conversation_faiss_index
            documents = ConversationFilesModel.objects.filter(conversation=conversation)
            if not faiss_index or not faiss_index.faiss_index_is_active:
                return False
            if not documents.exists():
                self.logger.warning(
                    f"No documents attached to conversation {conversation_key}.",
                    source=__file__,
                    call_by=self.check_documents_ready.__name__
                )
                return False  # No documents to wait for, consider it ready
            return True
        except ConversationModel.DoesNotExist:
            self.logger.error(
                f"Conversation not found: {conversation_key}",
                source=__file__,
                call_by=self.check_documents_ready.__name__
            )
            raise ValueError(f"Conversation not found: {conversation_key}")

    def generate_bootstrap_message(
        self,
        conversation_key: str,
        provider: EProviderName,
        model_name: str,
        prompt: str
    ) -> IConversationJobResponse:
        try:
            conversation = ConversationModel.objects.get(pk=conversation_key)
        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation not found: {conversation_key}")

        # Sinh câu trả lời bằng LLM
        assistant_message = self._generate_assistant_response(prompt, provider, model_name)

        # Lưu vào Database
        self._save_message(conversation, is_user_send=False, content=assistant_message)

        return IConversationJobResponse(
            conversation_id=str(conversation.conversation_id),
            assistant_message=assistant_message,
            provider=provider.value,
            model=model,
        )

    def _generate_assistant_response(self, prompt: str, provider: EProviderName, model_name: str) -> str:
        llm_client = self.llm_provider_factory.get_provider(provider)
        self.logger.info(
            f"Generating bootstrap message for conversation with provider={provider.value}",
            source=str(self.__class__),
            method_call=self._generate_assistant_response.__name__,
        )
        response = llm_client.generate(ICompletionRequest(provider=provider, model=model_name, prompt=prompt, context_hits=[]))
        return response

    def _save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        return MessageModel.objects.create(
            message_conversation=conversation,
            message_is_user_send=is_user_send,
            message_content=content,
        )
