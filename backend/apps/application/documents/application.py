"""
Document Application Layer.
Handles document upload business logic, validation, and orchestration.
"""

from typing import Optional, Dict, List, Any
from uuid import UUID
import logging
import hashlib
from pathlib import Path

from django.conf import settings
from backend.apps.services.chat.models import DocumentModel
from backend.apps.utils.path_file_helper import create_media_path

logger = logging.getLogger(__name__)


class DocumentApplication:
    """
    Application layer for document management.
    Handles business logic, validation, and coordination with job manager.
    """

    def __init__(self):
        """Initialize document application."""
        self.logger = logger
        self.storage_path = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path('./storage/media')

    def upload_document(
        self,
        file_content: bytes,
        file_name: str,
        conversation_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Process document upload and prepare for job scheduling.

        Args:
            file_content: Raw file bytes
            file_name: Name of the file
            conversation_id: Optional conversation ID to attach to

        Returns:
            Dictionary with document metadata for job manager

        Raises:
            ValueError: If validation fails
        """
        try:
            # Layer 2 Validation
            self._validate_upload_input(file_content, file_name)

            # Create storage path
            storage_dir = self.storage_path / "documents"
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Save file
            file_path = storage_dir / file_name
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Create document record
            document = DocumentModel.objects.create(
                faiss_index_file_name=file_name,
                file_path=str(file_path),
                status="uploaded",
            )

            self.logger.info(
                f"Created document {document.faiss_index_id} with file '{file_name}'"
            )

            # Prepare data for job manager
            document_request = {
                "file_id": str(document.faiss_index_id),
                "file_name": file_name,
                "file_path": str(file_path),
                "file_size": len(file_content),
                "conversation_id": str(conversation_id) if conversation_id else None,
                "content_hash": hashlib.sha256(file_content).hexdigest(),
            }

            return document_request

        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error uploading document: {e}")
            raise

    def get_document(self, document_id: UUID) -> Dict[str, Any]:
        """
        Get document details.

        Args:
            document_id: UUID of document

        Returns:
            Dictionary with document data

        Raises:
            ValueError: If document not found
        """
        try:
            document = DocumentModel.objects.get(pk=document_id)
            return self._serialize_document(document)
        except DocumentModel.DoesNotExist:
            raise ValueError(f"Document {document_id} not found")
        except Exception as e:
            self.logger.error(f"Error retrieving document: {e}")
            raise

    def list_documents(
        self, status: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """
        List documents with optional filtering.

        Args:
            status: Filter by status (e.g., 'indexed', 'processing')
            limit: Maximum number of documents to return
            offset: Offset for pagination

        Returns:
            Dictionary with documents list and metadata
        """
        try:
            query = DocumentModel.objects.all()

            if status:
                query = query.filter(status=status)

            total = query.count()
            documents_qs = query.order_by("-faiss_index_created_at")[
                offset : offset + limit
            ]

            documents = [self._serialize_document(d) for d in documents_qs]

            return {
                "documents": documents,
                "count": len(documents),
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            self.logger.error(f"Error listing documents: {e}")
            raise

    def update_document_status(
        self, document_id: UUID, status: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Update document status and metadata.

        Args:
            document_id: UUID of document
            status: New status ('uploaded', 'processing', 'indexed', 'failed')
            **kwargs: Additional fields to update (chunks_count, embedding_time, etc.)

        Returns:
            Updated document dictionary

        Raises:
            ValueError: If document not found or invalid status
        """
        try:
            # Validate status
            valid_statuses = ["uploaded", "processing", "indexed", "failed"]
            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid status '{status}'. Must be one of: {valid_statuses}"
                )

            document = DocumentModel.objects.get(pk=document_id)

            # Update status
            document.status = status

            # Store metadata in content field if needed (schema limitation)
            if kwargs:
                import json
                metadata = {
                    "status": status,
                    "extra": kwargs,
                }
                # Could extend model to store this properly
                self.logger.debug(f"Document {document_id} metadata: {metadata}")

            document.save()

            self.logger.info(
                f"Updated document {document_id} status to '{status}'"
            )

            return self._serialize_document(document)

        except DocumentModel.DoesNotExist:
            raise ValueError(f"Document {document_id} not found")
        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error updating document: {e}")
            raise

    def delete_document(self, document_id: UUID, delete_file: bool = True) -> None:
        """
        Delete document.

        Args:
            document_id: UUID of document
            delete_file: Whether to delete the file from storage

        Raises:
            ValueError: If document not found
        """
        try:
            document = DocumentModel.objects.get(pk=document_id)

            # Delete file from storage if requested
            if delete_file and document.file_path:
                file_path = Path(document.file_path)
                if file_path.exists():
                    try:
                        file_path.unlink()
                        self.logger.debug(f"Deleted file {document.file_path}")
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to delete file {document.file_path}: {e}"
                        )

            # Delete database record
            document.delete()
            self.logger.info(f"Deleted document {document_id}")

        except DocumentModel.DoesNotExist:
            raise ValueError(f"Document {document_id} not found")
        except Exception as e:
            self.logger.error(f"Error deleting document: {e}")
            raise

    # ==================== Private Helper Methods ====================

    def _validate_upload_input(self, file_content: bytes, file_name: str) -> None:
        """
        Validate upload input (Layer 2 validation).

        Args:
            file_content: Raw file bytes
            file_name: File name

        Raises:
            ValueError: If validation fails
        """
        if not file_content or not isinstance(file_content, bytes):
            raise ValueError("File content must be bytes")

        if not file_name or not isinstance(file_name, str):
            raise ValueError("File name must be a non-empty string")

        # Validate file name
        if len(file_name) > 255:
            raise ValueError("File name is too long (max 255 characters)")

        # Validate file size (max 500MB)
        max_size = 500 * 1024 * 1024
        if len(file_content) > max_size:
            raise ValueError(f"File size exceeds maximum allowed size of 500MB")

        # Validate file type
        allowed_extensions = [".pdf", ".txt", ".docx", ".doc", ".md"]
        file_ext = Path(file_name).suffix.lower()
        if file_ext not in allowed_extensions:
            raise ValueError(
                f"File type '{file_ext}' not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )

    def _serialize_document(self, document: DocumentModel) -> Dict[str, Any]:
        """
        Serialize document model to dictionary.

        Args:
            document: DocumentModel instance

        Returns:
            Dictionary representation
        """
        return {
            "id": str(document.faiss_index_id),
            "title": document.faiss_index_file_name,
            "status": document.status,
            "created_at": document.faiss_index_created_at.isoformat(),
            "is_active": document.faiss_index_is_active,
        }
