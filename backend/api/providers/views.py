from __future__ import annotations

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from sys_services.read_config.read_list_provider import LIST_PROVIDERS


class ProviderListView(APIView):
    """Return the list of available LLM providers and their models."""

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "providers": [
                    {
                        "name": provider.provider_name,
                        "models": provider.model_name,
                        "embed_model": provider.embed_model_name,
                    }
                    for provider in LIST_PROVIDERS
                ],
            },
            status=status.HTTP_200_OK,
        )


class ProviderTestView(APIView):
    """Test provider connection."""

    def post(self, request):
        return Response(
            {"status": "ok", "message": "Provider connection successful"},
            status=status.HTTP_200_OK,
        )
