from celery import shared_task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest

#! NOTE: CHANGE TO CLASS AND IMPLE INTERFACE ON 'interfaces/tasks/'

def _build_message_job():
    container = BackendContainer()
    return container.message_job()


def _resolve_provider(provider_name: str) -> EProviderName:
    try:
        return EProviderName(provider_name)
    except ValueError as exc:
        raise ValueError(f"Unsupported provider: {provider_name}") from exc


@shared_task
def send_message_task(
    conversation_id: str,
    content: str,
    provider_name: str = EProviderName.MISTRAL.value,
    model_name: str | None = None,
):
    provider = _resolve_provider(provider_name)
    message_job = _build_message_job()
    return message_job.run(
        conversation_id=conversation_id,
        content=content,
        provider=provider,
        model_name=model_name,
    )


@shared_task
def save_user_message_task(conversation_id: str, content: str):
    container = BackendContainer()
    message_job = _build_message_job()
    conversation = message_job._get_conversation(conversation_id)
    return message_job._save_message(conversation, is_user_send=True, content=content)


@shared_task
def build_message_context_task(conversation_id: str, content: str):
    container = BackendContainer()
    message_job = _build_message_job()
    conversation = message_job._get_conversation(conversation_id)
    document_texts = message_job._get_attached_document_texts(conversation)
    context_hits = message_job._retrieve_context_hits(content, document_texts)
    prompt = message_job._build_prompt(content, context_hits)
    return {
        "prompt": prompt,
        "context_hits": context_hits,
    }


@shared_task
def generate_assistant_response_task(
    prompt: str,
    provider_name: str = EProviderName.MISTRAL.value,
    model_name: str | None = None,
):
    provider = _resolve_provider(provider_name)
    container = BackendContainer()
    llm_client = container.llm_provider_factory()
    model = model_name or "gemini-2.5-flash"
    response = llm_client.generate(
        ICompletionRequest(
            provider=provider,
            model=model,
            prompt=prompt,
            context_hits=[],
        )
    )
    return {
        "assistant": response,
        "provider": provider_name,
        "model": model,
    }


@shared_task
def save_assistant_message_task(conversation_id: str, content: str):
    container = BackendContainer()
    message_job = _build_message_job()
    conversation = message_job._get_conversation(conversation_id)
    return message_job._save_message(conversation, is_user_send=False, content=content)
