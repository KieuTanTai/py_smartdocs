"""
Conversation tasks module.
Celery tasks for conversation processing.
"""

from celery import chain, shared_task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.job.conversation_job import DocumentsNotReadyError


def _build_conversation_job():
    container = BackendContainer()
    return container.conversation_job()


def _resolve_provider(provider_name: str) -> EProviderName:
    try:
        return EProviderName(provider_name)
    except ValueError as exc:
        raise ValueError(f"Unsupported provider: {provider_name}") from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def prepare_conversation(self, conversation_id: str, provider_name: str = EProviderName.MISTRAL.value, model_name: str | None = None):
    task_chain = chain(
        check_documents_ready.s(conversation_id),
        generate_bootstrap_message.s(conversation_id, provider_name, model_name),
    )
    result = task_chain.apply_async()
    return {"task_id": result.id}


@shared_task
def check_documents_ready(conversation_id: str):
    conversation_job = _build_conversation_job()
    return conversation_job.check_documents_ready(conversation_id)


@shared_task
def generate_bootstrap_message(
    is_ready: bool,
    conversation_id: str,
    provider_name: str = EProviderName.MISTRAL.value,
    model_name: str | None = None,
):
    if not is_ready:
        raise DocumentsNotReadyError(
            f"Documents attached to conversation {conversation_id} are not ready"
        )

    provider = _resolve_provider(provider_name)
    conversation_job = _build_conversation_job()
    return conversation_job.generate_bootstrap_message(
        conversation_id=conversation_id,
        provider=provider,
        model_name=model_name,
    )
