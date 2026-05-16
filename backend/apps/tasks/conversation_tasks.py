"""
Conversation tasks module.
Celery tasks for conversation processing.
"""

from celery import shared_task


@shared_task
async def prepare_conversation(conversation_id):
    # TODO: Background task to prepare conversation
    # Steps:
    # 1. Check if attached documents are indexed
    # 2. If documents not ready, retry later
    # 3. Generate bootstrap summary message
    # 4. Update conversation status to 'ready'
    pass


@shared_task
async def check_documents_ready(conversation_id):
    # TODO: Check if all attached documents are indexed
    pass


@shared_task
async def generate_bootstrap_message(conversation_id):
    # TODO: Generate initial assistant summary message
    pass
