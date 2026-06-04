from __future__ import annotations
import time
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class APIHealthView(APIView):
    """
    API view for health check.
    """

    def get(self, request):
        """
        Handle GET request for health check.
        Returns a JSON response with status "ok" and current timestamp.
        """
        return Response(
            {
                "status": "ok",
                "detail": "Backend is running",
                "timestamp": time.time(),
            },
            status=status.HTTP_200_OK,
        )