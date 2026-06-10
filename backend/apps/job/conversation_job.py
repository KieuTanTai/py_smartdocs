import time
from typing import List
import numpy as np
from pathlib import Path

# Import Interfaces
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, MessageModel

class ConversationJob(IConversationJob):


    def __init__(self, llm_provider_factory: ILLMProviderFactory, config_provider: IConfigProvider, logger: ILogger, hybrid_search_service: IHybridSearchService | None = None):
        self.llm_provider_factory = llm_provider_factory
        self.config_provider = config_provider
        self.logger = logger
        self.hybrid_search_service = hybrid_search_service

    def check_documents_ready(self, conversation_id: str) -> bool:
        try:
            conversation = ConversationModel.objects.get(pk=conversation_id)
            mappings = ConversationFilesModel.objects.filter(conversation=conversation)
            if not mappings.exists():
                return True
            for mapping in mappings:
                if mapping.faiss_index is None or mapping.faiss_index.status != "indexed":
                    return False
            return True
        except ConversationModel.DoesNotExist:
            self.logger.error(
                f"Conversation not found: {conversation_id}",
                source=__file__,
                call_by=self.check_documents_ready.__name__
            )
            raise ValueError(f"Conversation not found: {conversation_id}")

    def generate_bootstrap_message(self, conversation_id: str, provider: EProviderName, model_name: str | None = None) -> BootstrapMessageResponse:
        try:
            conversation = ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation not found: {conversation_id}")

        prompt = "Vui lòng chào người dùng và tóm tắt ngắn gọn các tài liệu đính kèm để bắt đầu hội thoại."
        model = model_name or "gemini-2.5-flash"
        
        # Sinh câu trả lời bằng LLM
        assistant_message = self._generate_assistant_response(prompt, provider, model)
        
        # Lưu vào Database
        self._save_message(conversation, is_user_send=False, content=assistant_message)
        
        return BootstrapMessageResponse(
            conversation_id=str(conversation.conversation_id),
            assistant_message=assistant_message,
            provider=provider.value,
            model=model
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