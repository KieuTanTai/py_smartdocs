"""
SmartDocs API URL Router
========================
Main URL configuration that delegates to sub-modules.
Each API domain (health, documents, conversations, providers, core) has its
own urls.py and views.py following the standard Django pattern.

NOTE: Most endpoints are commented out due to missing dependencies.
Only health check is enabled for testing.
"""
from django.urls import path, include

urlpatterns = [
    # Health check
    path("api/health/", include("backend.api.health.urls")),

    # Document endpoints
    path("api/documents/", include("backend.api.documents.urls")),

    # NOTE: Other endpoints disabled due to missing dependencies
    # Uncomment when all dependencies are installed
    # path("api/auth/", include("backend.api.auth.urls")),
    # path("api/conversations/", include("backend.api.conversations.urls")),
    # path("api/application/conversations/", include("backend.api.conversations.urls")),
    # path("api/providers/", include("backend.api.providers.urls")),
    # path("api/core/", include("backend.api.core.urls")),
]
