"""
Run Application Layer.
Handles full CRUD application orchestration: upload, send message, get/delete conversation.
Luồng layer: api/ → application/ → job/ → tasks/ → core/, llm/, services/
"""

from pathlib import Path
from typing import List, cast

from backend.apps.core.enums.e_document_status import EDocumentStatus
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.request.i_run_application_request import (
    IDeleteConversationApplicationRequest,
    ISendMessageApplicationRequest,
    IUploadApplicationRequest,
)
from backend.apps.core.interfaces.dataclass.response.i_run_application_response import (
    IGetConversationApplicationResponse,
    ISendMessageApplicationResponse,
    IUploadApplicationResponse,
)
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import IConversationDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.application.i_run_application import IRunApplication
from backend.apps.interfaces.job.i_delete_job import IDeleteJob
from backend.apps.interfaces.job.i_message_job import IMessageJob
from backend.apps.interfaces.job.i_upload_job import IUploadJob
from backend.apps.interfaces.tasks.i_upload_task import IUploadTask
from backend.apps.services.chat.models import (
    ConversationFilesModel,
    ConversationModel,
    DocumentModel,
    MessageModel,
)


class RunApplication(IRunApplication):
    """Application layer tổng hợp cho full CRUD.
    Validate nghiệp vụ, chuẩn bị dữ liệu, handle exception, gọi job nền, flush log.
    Tất cả dependency được inject qua constructor (IoC/DI).
    """

    def __init__(
        self,
        upload_task: IUploadTask,
        message_job: IMessageJob,
        delete_job: IDeleteJob,
        database_provider: IDatabaseProvider,
        logger: ILogger,
    ):
        self.upload_task = upload_task
        self.message_job = message_job
        self.delete_job = delete_job
        self.database_provider = database_provider
        self.logger = logger
        self.conversation_database = cast(
            IConversationDatabase,
            self.database_provider.get_model_service(ConversationModel),
        )

    def upload(self, request: IUploadApplicationRequest) -> IUploadApplicationResponse:
        """Upload tài liệu: tạo conversation → chạy pipeline → summarize → trả response.
        Flow chuẩn rule mục 4: tạo conversation trước, rồi mới process file.
        Upload fail → xóa conversation vừa tạo.
        """
        try:
            # Validate nghiệp vụ
            self._validate_upload_request(request)

            # Tạo conversation trước (rule mục 4: tạo conversation trước, rồi mới process file)
            conversation = self._create_conversation_for_upload(request)
            conversation_id = str(conversation.conversation_id)

            try:
                # Chạy pipeline upload qua upload_task (extract → normalize → chunk → embed → save)
                upload_response = self.upload_task.run_with_paths(
                    conversation_model=conversation,
                    file_paths=request.document_paths,
                    provider_name=request.provider,
                    model_name=request.model_name,
                    file_caller=self.upload.__name__,
                )

                # Lưu summarize message vào conversation (rule mục 4)
                if upload_response.summarize:
                    self._save_summary_message(conversation, upload_response.summarize)

                # Tạo conversation files mapping
                self._create_conversation_files(conversation, upload_response.faiss_file_id)

                self.logger.info(
                    f"Upload completed for conversation {conversation_id} with {len(request.document_paths)} files",
                    source=Path(__file__).name,
                    call_by=self.upload.__name__,
                )

                return IUploadApplicationResponse(
                    id=str(upload_response.faiss_file_id),
                    title=conversation.conversation_title or "",
                    status=EDocumentStatus.INDEXED.value,
                    conversation_id=conversation_id,
                    date_create=conversation.conversation_created_at.isoformat()
                    if conversation.conversation_created_at
                    else "",
                )

            except Exception as exc:
                # Upload fail → xóa conversation vừa tạo (rule mục 4)
                self.logger.error(
                    f"Upload failed for conversation {conversation_id}, removing conversation: {exc}",
                    source=Path(__file__).name,
                    call_by=self.upload.__name__,
                )
                self._remove_conversation(conversation_id)
                raise exc

        except ValueError as exc:
            self.logger.error(
                f"Validation error in upload: {exc}",
                source=Path(__file__).name,
                call_by=self.upload.__name__,
            )
            raise exc
        except Exception as exc:
            self.logger.error(
                f"Unexpected error in upload: {exc}",
                source=Path(__file__).name,
                call_by=self.upload.__name__,
            )
            raise exc
        finally:
            # Flush log ở class cấp cao nhất (rule mục 10)
            self.logger.flush()

    def send_message(self, request: ISendMessageApplicationRequest) -> ISendMessageApplicationResponse:
        """Gửi tin nhắn chat: validate → RAG retrieval → LLM generate → trả response."""
        try:
            # Validate nghiệp vụ
            self._validate_send_message_request(request)

            # Gọi message_job.run() (hybrid search + LLM generate)
            message_response = self.message_job.run(
                conversation_id=request.conversation_id,
                content=request.message,
                provider=request.provider,
                model_name=request.model_name,
            )

            self.logger.info(
                f"Message sent for conversation {request.conversation_id}",
                source=Path(__file__).name,
                call_by=self.send_message.__name__,
            )

            return ISendMessageApplicationResponse(
                message=message_response.assistant,
                used_mock=False,
                conversation_id=message_response.conversation_id,
            )

        except ValueError as exc:
            self.logger.error(
                f"Validation error in send_message: {exc}",
                source=Path(__file__).name,
                call_by=self.send_message.__name__,
            )
            raise exc
        except Exception as exc:
            self.logger.error(
                f"Unexpected error in send_message: {exc}",
                source=Path(__file__).name,
                call_by=self.send_message.__name__,
            )
            raise exc
        finally:
            self.logger.flush()

    def get_conversation(self, conversation_id: str) -> IGetConversationApplicationResponse:
        """Lấy thông tin conversation."""
        try:
            conversation = self.conversation_database.get_by_id(conversation_id)
            return self._serialize_conversation(conversation)
        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except Exception as exc:
            self.logger.error(
                f"Error retrieving conversation {conversation_id}: {exc}",
                source=Path(__file__).name,
                call_by=self.get_conversation.__name__,
            )
            raise exc

    def list_conversations(self) -> List[IGetConversationApplicationResponse]:
        """Lấy danh sách tất cả conversations."""
        try:
            conversations = self.conversation_database.list()
            return [self._serialize_conversation(c) for c in conversations]
        except Exception as exc:
            self.logger.error(
                f"Error listing conversations: {exc}",
                source=Path(__file__).name,
                call_by=self.list_conversations.__name__,
            )
            raise exc

    def delete_conversation(self, request: IDeleteConversationApplicationRequest) -> None:
        """Xóa conversation và tất cả dữ liệu liên quan.
        Rule mục 9: DB chỉ động tới khi xóa conversation — xóa sạch cả message, file, mapping.
        """
        try:
            conversation_id = request.conversation_id

            # Validate conversation exists
            conversation = self.conversation_database.get_by_id(conversation_id)

            # Lấy tất cả document IDs liên quan
            file_mappings = ConversationFilesModel.objects.filter(conversation=conversation)
            document_ids = [str(mapping.faiss_index_id) for mapping in file_mappings if mapping.faiss_index_id]

            # Dọn dẹp RAG data cho từng document (FAISS, BM25, Cache, Graph)
            for doc_id in document_ids:
                try:
                    self.delete_job.step_clear_cache(doc_id, file_caller=self.delete_conversation.__name__)
                    self.delete_job.step_delete_vectors(doc_id, file_caller=self.delete_conversation.__name__)
                    self.delete_job.step_delete_graph_data(doc_id, file_caller=self.delete_conversation.__name__)
                except Exception as exc:
                    self.logger.warning(
                        f"Non-critical error cleaning RAG data for document {doc_id}: {exc}",
                        source=Path(__file__).name,
                        call_by=self.delete_conversation.__name__,
                    )

            # Xóa conversation (cascade sẽ xóa messages, files mapping)
            self.conversation_database.delete(conversation_id)

            self.logger.info(
                f"Deleted conversation {conversation_id} with {len(document_ids)} documents",
                source=Path(__file__).name,
                call_by=self.delete_conversation.__name__,
            )

        except ConversationModel.DoesNotExist:
            raise ValueError(f"Conversation {conversation_id} not found")
        except ValueError:
            raise
        except Exception as exc:
            self.logger.error(
                f"Error deleting conversation {request.conversation_id}: {exc}",
                source=Path(__file__).name,
                call_by=self.delete_conversation.__name__,
            )
            raise exc
        finally:
            self.logger.flush()

    # ==================== Private Helper Methods ====================

    def _validate_upload_request(self, request: IUploadApplicationRequest) -> None:
        """Validate upload request (Layer 2 validation - nghiệp vụ)."""
        if not request.document_paths and not request.document_urls:
            raise ValueError("At least one document_path or document_url is required")

        if request.document_paths and len(request.document_paths) > 3:
            raise ValueError("Maximum 3 files per upload (rule: giới hạn FE tối đa 3 file/lần)")

        for path in request.document_paths:
            if not path.exists():
                raise ValueError(f"File not found: {path}")

        if request.type not in ("normal", "graph"):
            raise ValueError(f"Invalid pipeline type '{request.type}'. Must be 'normal' or 'graph'")

    def _validate_send_message_request(self, request: ISendMessageApplicationRequest) -> None:
        """Validate send message request (Layer 2 validation - nghiệp vụ)."""
        if not request.conversation_id:
            raise ValueError("conversation_id is required")

        if not request.message or not request.message.strip():
            raise ValueError("message must be a non-empty string")

        if not request.model_name:
            raise ValueError("model_name is required")

    def _create_conversation_for_upload(self, request: IUploadApplicationRequest) -> ConversationModel:
        """Tạo conversation mới cho upload."""
        file_names = [p.name for p in request.document_paths]
        title = ", ".join(file_names) if file_names else "New Conversation"
        conversation_name = "_".join(file_names) if file_names else ""

        conversation = self.conversation_database.create_conversation(
            conversations_name=conversation_name,
            conversations_title=title,
        )

        self.logger.info(
            f"Created conversation {conversation.conversation_id} for upload with title '{title}'",
            source=Path(__file__).name,
            call_by=self._create_conversation_for_upload.__name__,
        )

        return conversation

    def _save_summary_message(self, conversation: ConversationModel, summary: str) -> None:
        """Lưu message summarize vào conversation (rule mục 4)."""
        MessageModel.objects.create(
            message_conversation=conversation,
            message_is_user_send=False,
            message_content=summary,
        )

    def _create_conversation_files(self, conversation: ConversationModel, document_id) -> None:
        """Tạo conversation files mapping."""
        try:
            document = DocumentModel.objects.get(pk=document_id)
            ConversationFilesModel.objects.create(
                conversation=conversation,
                faiss_index=document,
            )
        except DocumentModel.DoesNotExist:
            self.logger.warning(
                f"Document {document_id} not found when creating conversation files mapping",
                source=Path(__file__).name,
                call_by=self._create_conversation_files.__name__,
            )

    def _remove_conversation(self, conversation_id: str) -> None:
        """Xóa conversation khi upload fail (rule mục 4)."""
        try:
            self.conversation_database.delete(conversation_id)
        except Exception as exc:
            self.logger.error(
                f"Failed to remove conversation {conversation_id} after upload failure: {exc}",
                source=Path(__file__).name,
                call_by=self._remove_conversation.__name__,
            )

    def _serialize_conversation(self, conversation: ConversationModel) -> IGetConversationApplicationResponse:
        """Serialize conversation model to response dataclass."""
        return IGetConversationApplicationResponse(
            conversation_id=str(conversation.conversation_id),
            status="ready",
            date_create=conversation.conversation_created_at.isoformat()
            if conversation.conversation_created_at
            else "",
            title=conversation.conversation_title,
        )
