"""
SmartDocs API URL Router
========================
Main URL configuration that delegates to sub-modules.
Each API domain (health, documents, conversations, providers, core) has its
own urls.py and views.py following the standard Django pattern.
"""
from django.urls import path, include

urlpatterns = [
    # Health check
    path("api/health/", include("backend.api.health.urls")),

    # Authentication (signup, login, logout)
    path("api/auth/", include("backend.api.auth.urls")),

    # Document management
    path("api/documents/", include("backend.api.documents.urls")),

    # Conversations & messages
    path("api/conversations/", include("backend.api.conversations.urls")),

    # Backward compatibility: /api/application/conversations/ → same views
    path("api/application/conversations/", include("backend.api.conversations.urls")),

    # LLM Providers
    path("api/providers/", include("backend.api.providers.urls")),

    # Core search
    path("api/core/", include("backend.api.core.urls")),
]
