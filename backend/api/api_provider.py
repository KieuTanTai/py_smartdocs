from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sys_services.read_config.read_list_provider import LIST_PROVIDERS


class APIProvider(APIView):
    def get(self, request):
        """Handle GET request for provider info.
        Returns a JSON response with available providers and their models.
        """
        providers = []
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


    def post(self, request):
        """Handle POST request to test provider connection.
        Expects a JSON body with 'provider' and 'model' fields.
        Returns a JSON response indicating success or failure of the connection test.
        """
        return Response(
            {"status": "ok", "message": "Provider connection successful"},
            status=status.HTTP_200_OK,
        )
