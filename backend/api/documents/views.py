from __future__ import annotations

import os
from pathlib import Path

import pypdf
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from backend.apps.services.chat.models import DocumentModel
from backend.apps.core.normalize.normalize import Normalize
from sys_services.logging import DEFAULT_LOGGER


class DocumentListView(APIView):
    def get(self, request):
        docs = DocumentModel.objects.all().order_by("-faiss_index_created_at")
        data = []
        for d in docs:
            data.append({
                "id": str(d.faiss_index_id),
                "title": d.faiss_index_file_name,
                "status": d.status,
                "source": "local"
            })
        return Response(data, status=status.HTTP_200_OK)


class DocumentUploadView(APIView):
    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # Save file to media directory
        media_dir = Path(settings.MEDIA_ROOT)
        media_dir.mkdir(parents=True, exist_ok=True)
        file_path = media_dir / uploaded_file.name

        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Create DocumentModel record
        doc = DocumentModel.objects.create(
            faiss_index_file_name=uploaded_file.name,
            file_path=str(file_path),
            status="uploaded"
        )

        return Response({
            "id": str(doc.faiss_index_id),
            "title": doc.faiss_index_file_name,
            "status": "uploaded"
        }, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    def get(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            return Response({
                "id": str(doc.faiss_index_id),
                "title": doc.faiss_index_file_name,
                "status": doc.status
            }, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except Exception:
                    pass
            doc.delete()
            return Response({"status": "deleted"}, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)


class DocumentStatusView(APIView):
    def get(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            return Response({
                "id": str(doc.faiss_index_id),
                "status": doc.status
            }, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)


class DocumentIndexView(APIView):
    def post(self, request, document_id: str):
        try:
            doc = DocumentModel.objects.get(pk=document_id)
            doc.status = "processing"
            doc.save()

            # Read file and extract text
            extracted_text = ""
            if doc.file_path and os.path.exists(doc.file_path):
                if doc.file_path.endswith(".pdf"):
                    try:
                        reader = pypdf.PdfReader(doc.file_path)
                        text_list = []
                        for page in reader.pages:
                            t = page.extract_text()
                            if t:
                                text_list.append(t)
                        extracted_text = "\n".join(text_list)
                    except Exception as e:
                        DEFAULT_LOGGER.error(f"Failed to read PDF: {e}")
                elif doc.file_path.endswith(".docx"):
                    try:
                        import zipfile
                        import xml.etree.ElementTree as ET
                        with zipfile.ZipFile(doc.file_path) as docx:
                            xml_content = docx.read('word/document.xml')
                            root = ET.fromstring(xml_content)
                            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                            paragraphs = []
                            for p in root.findall('.//w:p', ns):
                                text_runs = [t.text for t in p.findall('.//w:t', ns) if t.text]
                                if text_runs:
                                    paragraphs.append(''.join(text_runs))
                            extracted_text = '\n'.join(paragraphs)
                    except Exception as e:
                        DEFAULT_LOGGER.error(f"Failed to read DOCX: {e}")
                else:
                    try:
                        with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
                            extracted_text = f.read()
                    except Exception as e:
                        DEFAULT_LOGGER.error(f"Failed to read text file: {e}")

            # Normalize text
            normalizer = Normalize()
            normalized_text = normalizer.normalize(extracted_text)

            doc.content = normalized_text
            doc.status = "indexed"
            doc.save()

            return Response({
                "id": str(doc.faiss_index_id),
                "status": "indexed"
            }, status=status.HTTP_200_OK)
        except DocumentModel.DoesNotExist:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)


class DocumentBulkIndexView(APIView):
    def post(self, request):
        return Response({"detail": "Not implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED)
