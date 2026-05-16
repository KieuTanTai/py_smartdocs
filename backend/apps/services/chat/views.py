"""
Chat views.
DRF ViewSets for conversation and message endpoints.
"""


class ConversationViewSet:
    """
    ViewSet for conversation management.

    Endpoints:
        GET /api/application/conversations/ - List conversations
        POST /api/application/conversations/ - Create conversation
        GET /api/application/conversations/{id}/ - Conversation detail
        GET /api/application/conversations/{id}/status/ - Readiness status
        PATCH /api/application/conversations/{id}/documents/ - Update documents
    """

    def __init__(self):
        # TODO: Initialize conversation ViewSet
        pass

    def list(self, request):
        # TODO: List all conversations
        pass

    def create(self, request):
        # TODO: Create new conversation with document attachments
        pass

    def retrieve(self, request, pk=None):
        # TODO: Get conversation details
        pass

    def get_status(self, request, pk=None):
        # TODO: Get conversation readiness status
        pass

    def update_documents(self, request, pk=None):
        # TODO: Update attached documents
        pass


class MessageViewSet:
    """
    ViewSet for message management.

    Endpoints:
        GET /api/application/conversations/{id}/messages/ - List messages
        POST /api/application/conversations/{id}/messages/ - Send message
    """

    def __init__(self):
        # TODO: Initialize message ViewSet
        pass

    def list(self, request, conversation_pk=None):
        # TODO: Get conversation history
        pass

    def create(self, request, conversation_pk=None):
        # TODO: Send user message and get response
        # Process: save message -> search -> build context -> call LLM -> save response
        pass
