"""
Document API Views - Mock version for development
Simplified implementations without heavy dependencies
"""
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class DocumentListView(APIView):
    """Mock document list view for testing"""
    def get(self, request):
        # Mock response - replace with actual implementation when dependencies are installed
        data = []
        return Response(data, status=status.HTTP_200_OK)


class DocumentUploadView(APIView):
    """Mock document upload view for testing"""
    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "id": "mock-id-123",
            "title": uploaded_file.name,
            "status": "uploaded"
        }, status=status.HTTP_201_CREATED)



class DocumentDetailView(APIView):
    """Get or delete a specific document"""
    def get(self, request, document_id: str):
        return Response({
            "id": document_id,
            "title": "Mock Document",
            "status": "uploaded"
        }, status=status.HTTP_200_OK)

    def delete(self, request, document_id: str):
        return Response({"status": "deleted"}, status=status.HTTP_200_OK)


class DocumentStatusView(APIView):
    """Get document status"""
    def get(self, request, document_id: str):
        return Response({
            "id": document_id,
            "status": "indexed"
        }, status=status.HTTP_200_OK)


class DocumentIndexView(APIView):
    """Index a document (mock version)"""
    def post(self, request, document_id: str):
        return Response({
            "id": document_id,
            "status": "indexed",
            "chunks": 42,
            "dimensions": 1536
        }, status=status.HTTP_200_OK)


class DocumentBulkIndexView(APIView):
    """Bulk index documents (mock)"""
    def post(self, request):
        return Response({"detail": "Bulk indexing mock"}, status=status.HTTP_200_OK)

