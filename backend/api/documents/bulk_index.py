"""
Bulk document indexing endpoint.
POST /api/documents/index/bulk/
Accepts a list of document IDs and schedules them for async indexing via Celery.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.services.chat.models import DocumentModel
from backend.apps.tasks import index_document, bulk_index_documents
from sys_services.logging import DEFAULT_LOGGER

_cached_celery = None


def _get_celery_task():
    global _cached_celery
    if _cached_celery is None:
        from app.settings.local import get_celery_app
        _cached_celery = get_celery_app()
    return _cached_celery


class DocumentBulkIndexView(APIView):
    """
    POST /api/documents/index/bulk/
    Body: { "document_ids": ["uuid1", "uuid2", ...] }
    Returns: { "total": int, "results": [...], "celery_available": bool }
    """

    def post(self, request):
        raw_ids = request.data.get("document_ids") or []

        if not isinstance(raw_ids, list) or not raw_ids:
            return Response(
                {"error": "document_ids must be a non-empty list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate documents exist
        valid_ids: list[str] = []
        invalid_ids: list[str] = []
        for doc_id in raw_ids:
            doc_id_str = str(doc_id).strip()
            if not doc_id_str:
                continue
            try:
                DocumentModel.objects.get(pk=doc_id_str)
                valid_ids.append(doc_id_str)
            except Exception:
                invalid_ids.append(doc_id_str)

        if not valid_ids:
            return Response(
                {"error": "No valid documents found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        celery_app = _get_celery_task()

        if celery_app is not None:
            # Dispatch via Celery (async)
            results = []
            for doc_id in valid_ids:
                try:
                    task = index_document.delay(doc_id)
                    results.append({
                        "document_id": doc_id,
                        "celery_task_id": task.id,
                        "status": "queued",
                    })
                except Exception as exc:
                    DEFAULT_LOGGER.error(
                        f"Failed to queue Celery task for {doc_id}: {exc}",
                        source="DocumentBulkIndexView",
                    )
                    results.append({
                        "document_id": doc_id,
                        "error": str(exc),
                        "status": "failed",
                    })

            DEFAULT_LOGGER.info(
                f"Bulk index: queued {len(results)} documents via Celery.",
                source="DocumentBulkIndexView",
            )
            return Response({
                "total": len(valid_ids),
                "results": results,
                "celery_available": True,
                "invalid_ids": invalid_ids,
            }, status=status.HTTP_202_ACCEPTED)

        else:
            # Celery not available — fallback: process synchronously (one by one)
            results = []
            for doc_id in valid_ids:
                try:
                    result = index_document(doc_id)
                    results.append({
                        "document_id": doc_id,
                        "status": result.get("status", "indexed"),
                        "chunks": result.get("chunks", 0),
                    })
                except Exception as exc:
                    results.append({
                        "document_id": doc_id,
                        "error": str(exc),
                        "status": "failed",
                    })

            DEFAULT_LOGGER.info(
                f"Bulk index: processed {len(results)} documents synchronously (no Celery).",
                source="DocumentBulkIndexView",
            )
            return Response({
                "total": len(valid_ids),
                "results": results,
                "celery_available": False,
                "invalid_ids": invalid_ids,
            }, status=status.HTTP_200_OK)
