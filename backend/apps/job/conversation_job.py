import time
from typing import List

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.services.chat.models import ConversationFilesModel, ConversationModel, MessageModel


class DocumentsNotReadyError(ValueError):
    pass


class ConversationJob:
    """Job that prepares a conversation for chat.

    Flow:
      1. Verify attached documents are indexed
      2. Build retrieval context from attached documents
      3. Generate bootstrap assistant message
      4. Save assistant message and return conversation info
    """

    def __init__(
        self,
        llm_provider_factory: ILLMProviderFactory,
        config_provider: IConfigProvider,
        logger: ILogger,
    ):
        self.llm_provider_factory = llm_provider_factory
        self.config_provider = config_provider
        self.logger = logger

    def prepare_conversation(
        self,
        conversation_id: str,
        provider: EProviderName,
        model_name: str | None = None,
    ) -> dict:
        conversation = self._get_conversation(conversation_id)

        if not self._documents_ready(conversation):
            raise DocumentsNotReadyError(
                f"Documents attached to conversation {conversation_id} are not ready"
            )

        prompt, context_hits = self._build_prompt(conversation)
        answer = self._generate_assistant_response(prompt, provider, model_name)
        self._save_message(conversation, is_user_send=False, content=answer)

        return {
            "conversation_id": str(conversation.conversation_id),
            "status": "ready",
            "assistant": answer,
            "provider": provider,
            "model": model_name or "qwen2.5:1.5b-instruct",
            "retrieval_hits": context_hits,
        }

    def check_documents_ready(self, conversation_id: str) -> bool:
        conversation = self._get_conversation(conversation_id)
        return self._documents_ready(conversation)

    def generate_bootstrap_message(
        self,
        conversation_id: str,
        provider: EProviderName,
        model_name: str | None = None,
    ) -> dict:
        conversation = self._get_conversation(conversation_id)
        prompt, context_hits = self._build_prompt(conversation)
        answer = self._generate_assistant_response(prompt, provider, model_name)
        self._save_message(conversation, is_user_send=False, content=answer)
        return {
            "conversation_id": str(conversation.conversation_id),
            "assistant": answer,
            "provider": provider,
            "model": model_name or "qwen2.5:1.5b-instruct",
            "retrieval_hits": context_hits,
        }

    def _get_conversation(self, conversation_id: str) -> ConversationModel:
        try:
            return ConversationModel.objects.get(pk=conversation_id)
        except ConversationModel.DoesNotExist as exc:
            raise ValueError(f"Conversation not found: {conversation_id}") from exc

    def _documents_ready(self, conversation: ConversationModel) -> bool:
        mappings = ConversationFilesModel.objects.filter(conversation=conversation)
        for mapping in mappings:
            if mapping.faiss_index is None or mapping.faiss_index.status != "indexed":
                return False
        return True

    def _get_attached_document_texts(self, conversation: ConversationModel) -> List[str]:
        texts: List[str] = []
        mappings = ConversationFilesModel.objects.filter(conversation=conversation)
        for mapping in mappings:
            if mapping.faiss_index and mapping.faiss_index.content:
                texts.append(mapping.faiss_index.content)
        return texts

    def _build_prompt(self, conversation: ConversationModel) -> tuple[str, List[dict]]:
        document_texts = self._get_attached_document_texts(conversation)
        paragraphs: List[str] = []
        for doc_text in document_texts:
            paragraphs.extend([p.strip() for p in doc_text.split("\n") if p.strip()])

        top_paragraphs = paragraphs[:5]
        context_text = "\n".join(top_paragraphs)
        context_hits = [
            {"text": paragraph[:200] + "...", "score": idx + 1}
            for idx, paragraph in enumerate(top_paragraphs)
        ]

        system_prompt = "You are a helpful assistant."
        prompt = (
            f"System prompt: {system_prompt}\n\n"
            f"Context from attached documents:\n{context_text}\n\n"
            f"Assistant: Please summarize the attached documents and explain how the conversation can proceed."
        )

        return prompt, context_hits

    def _generate_assistant_response(
        self,
        prompt: str,
        provider: EProviderName,
        model_name: str | None = None,
    ) -> str:
        llm_client = self.llm_provider_factory.get_provider(provider)
        model = model_name or "qwen2.5:1.5b-instruct"
        self.logger.info(
            f"Generating bootstrap message for conversation with provider={provider}",
            source=str(self.__class__),
            method_call=self._generate_assistant_response.__name__,
        )
        response = llm_client.generate(
            ICompletionRequest(
                provider=provider,
                model=model,
                prompt=prompt,
                context_hits=[],
            )
        )
        return response

    def _save_message(
        self,
        conversation: ConversationModel,
        is_user_send: bool,
        content: str,
    ) -> MessageModel:
        return MessageModel.objects.create(
            message_conversation=conversation,
            message_is_user_send=is_user_send,
            message_content=content,
        )
