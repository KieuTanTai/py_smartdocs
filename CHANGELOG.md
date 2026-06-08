# CHANGELOG — DỰ ÁN SMARTDOCS (py_smartdocs)

> Tệp này liệt kê **toàn bộ** các file đã thêm mới, chỉnh sửa, đổi tên và xoá trong dự án, 
> tính từ commit đầu tiên (`35d2237`) đến trạng thái hiện tại (bao gồm cả thay đổi chưa commit).
>
> **Ký hiệu**: 🆕 Thêm mới · ✏️ Chỉnh sửa · 🔄 Đổi tên / Di chuyển · 🗑️ Xoá

---

## I. CẤU HÌNH DỰ ÁN DJANGO (Chưa commit — Mới tạo)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [manage.py](file:///c:/py_smartdocs/manage.py) | Entry point CLI của Django, thiết lập `DJANGO_SETTINGS_MODULE=app.settings.local` |
| 🆕 | [app/\_\_init\_\_.py](file:///c:/py_smartdocs/app/__init__.py) | Module init cho package `app` |
| 🆕 | [app/urls.py](file:///c:/py_smartdocs/app/urls.py) | Root URL config — import `urlpatterns` từ `backend.api.gateway`, phục vụ media files khi `DEBUG=True` |
| 🆕 | [app/wsgi.py](file:///c:/py_smartdocs/app/wsgi.py) | WSGI application entry point |
| 🆕 | [app/asgi.py](file:///c:/py_smartdocs/app/asgi.py) | ASGI application entry point |
| 🆕 | [app/settings/local.py](file:///c:/py_smartdocs/app/settings/local.py) | Django settings đầy đủ: `INSTALLED_APPS`, `DATABASES` (SQLite fallback + MariaDB), `MIDDLEWARE`, `MEDIA_ROOT`, `REST_FRAMEWORK` |

---

## II. BACKEND — API Gateway

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [backend/api/gateway.py](file:///c:/py_smartdocs/backend/api/gateway.py) | Tạo REST API skeleton với các view: Health, Provider, Document, Conversation, Message, Search. Ban đầu trả `501 Not Implemented` |
| ✏️ | [backend/api/gateway.py](file:///c:/py_smartdocs/backend/api/gateway.py) | **(Chưa commit)** Triển khai logic thực tế cho hầu hết API views: `DocumentUploadView` (lưu file vào `storage/media`), `ConversationListView`/`DetailView` (CRUD conversation qua Django ORM), `MessageListView` (gửi tin nhắn + gọi LLM qua pipeline: extract context → vector search → generate), thêm `AuthLoginView` và `AuthSignupView` |

---

## III. BACKEND — Config & DI Container

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [backend/apps/config/container.py](file:///c:/py_smartdocs/backend/apps/config/container.py) | IoC container (dependency-injector): đăng ký Logger, Storage, Extract, Locate services |
| ✏️ | [backend/apps/config/container.py](file:///c:/py_smartdocs/backend/apps/config/container.py) | **(Chưa commit)** Sửa từ interface → implementation class thực tế (`LLMOCRFactory`, `MistralUploader`, `FileStorageService`, `ExtractContentService`, `LocateService`) |
| 🆕 | [backend/apps/config/settings.py](file:///c:/py_smartdocs/backend/apps/config/settings.py) | Khai báo các đường dẫn config mặc định |

---

## IV. BACKEND — Core Interfaces (Abstract Layer)

### Interfaces gốc (Core)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [base.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/base.py) | Abstract base interface cho toàn bộ hệ thống |
| 🆕 | [core/chunk/i_chunking.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/core/chunk/i_chunking.py) | Interface cho chunking module |
| 🆕 | [core/i_dataclass_transaction.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/core/i_dataclass_transaction.py) | Dataclass cho completion request (migrate từ `i_completion`) |
| 🆕 | [core/normalize/i_normalize.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/core/normalize/i_normalize.py) | Interface cho normalize module |

### Interfaces — LLM

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [llm/i_llm_client.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/llm/i_llm_client.py) | Interface cho LLM client (generate, embed) |
| 🆕 | [llm/i_llm_prompt_structure.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/llm/i_llm_prompt_structure.py) | Interface cho prompt structure |
| 🆕 | [llm/i_llm_provider_factory.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/llm/i_llm_provider_factory.py) | Interface cho LLM provider factory pattern |
| 🆕 | [llm/llm_ocr/i_llm_ocr.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/llm/llm_ocr/i_llm_ocr.py) | Interface cho OCR via LLM |
| 🆕 | [llm/llm_ocr/i_llm_ocr_factory.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/llm/llm_ocr/i_llm_ocr_factory.py) | Interface cho OCR factory |
| 🆕 | [llm/llm_ocr/i_llm_uploader.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/llm/llm_ocr/i_llm_uploader.py) | Interface cho file uploader (Mistral storage) |

### Interfaces — Services (RAG, Graph, Storage)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [services/graph_rag/i_graph.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/graph_rag/i_graph.py) | Interface cho Graph RAG service |
| 🆕 | [services/rag_base/extract/i_extract_content.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/rag_base/extract/i_extract_content.py) | Interface trích xuất nội dung từ file |
| 🆕 | [services/rag_base/locate/i_embed_storage_result.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/rag_base/locate/i_embed_storage_result.py) | Dataclass kết quả embed + storage |
| 🆕 | [services/rag_base/locate/i_locate_service.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/rag_base/locate/i_locate_service.py) | Interface cho locate/retrieval service |
| 🆕 | [services/rag_base/locate/i_vector_store_service.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/rag_base/locate/i_vector_store_service.py) | Interface cho vector store (FAISS/Qdrant) |
| 🆕 | [services/rag_base/storage/i_create_file_response.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/rag_base/storage/i_create_file_response.py) | Dataclass response tạo file |
| 🆕 | [services/rag_base/storage/i_get_file_response.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/rag_base/storage/i_get_file_response.py) | Dataclass response lấy file |
| 🆕 | [services/rag_base/storage/i_storage.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/services/rag_base/storage/i_storage.py) | Interface cho file storage service |

### Interfaces — System

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [system/i_config.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/system/i_config.py) | Interface cho config reader |
| 🆕 | [system/i_logging.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/system/i_logging.py) | Interface cho logging |
| 🆕 | [system/i_time_counter.py](file:///c:/py_smartdocs/backend/apps/core/interfaces/system/i_time_counter.py) | Interface cho time counter (benchmark) |

### Interfaces — Outer Layer (Job, Chat)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [interfaces/job/i_job_management.py](file:///c:/py_smartdocs/backend/apps/interfaces/job/i_job_management.py) | Interface cho job/task management |
| 🆕 | [interfaces/job/i_time_counter.py](file:///c:/py_smartdocs/backend/apps/interfaces/job/i_time_counter.py) | Interface cho time counter (outer layer) |
| 🆕 | [interfaces/services/chat/i_conversation.py](file:///c:/py_smartdocs/backend/apps/interfaces/services/chat/i_conversation.py) | Interface cho conversation service |
| 🆕 | [interfaces/services/chat/i_message.py](file:///c:/py_smartdocs/backend/apps/interfaces/services/chat/i_message.py) | Interface cho message service |
| 🆕 | [interfaces/services/chat/i_search.py](file:///c:/py_smartdocs/backend/apps/interfaces/services/chat/i_search.py) | Interface cho semantic search |
| 🆕 | [interfaces/services/chat/i_summarization.py](file:///c:/py_smartdocs/backend/apps/interfaces/services/chat/i_summarization.py) | Interface cho summarization |

---

## V. BACKEND — Implementations (Core Logic)

### Xử lý văn bản (Chunking, Normalize)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [core/chunk/chunker.py](file:///c:/py_smartdocs/backend/apps/core/chunk/chunker.py) | Chunking sử dụng `NLTKTextSplitter` với fallback manual split |
| 🆕 | [core/normalize/normalize.py](file:///c:/py_smartdocs/backend/apps/core/normalize/normalize.py) | Chuẩn hóa text bằng regex (khoảng trắng, dòng trống) |

### LLM Clients

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [llm/gemini.py](file:///c:/py_smartdocs/backend/apps/llm/gemini.py) | Adapter cho Google Gemini (generate + embed) |
| 🆕 | [llm/mistral.py](file:///c:/py_smartdocs/backend/apps/llm/mistral.py) | Adapter cho Mistral AI (generate + embed) |
| 🆕 | [llm/ollama.py](file:///c:/py_smartdocs/backend/apps/llm/ollama.py) | Adapter cho Ollama local models (Qwen2.5:3b) |
| 🆕 | [llm/llm_prompt_structure.py](file:///c:/py_smartdocs/backend/apps/llm/llm_prompt_structure.py) | Xây dựng prompt structure cho LLM |
| 🆕 | [llm/llm_provider_factory.py](file:///c:/py_smartdocs/backend/apps/llm/llm_provider_factory.py) | Factory pattern: chọn LLM provider theo config |

### LLM OCR (Trích xuất bằng AI)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [llm/llm_ocr/llm_ocr_factory.py](file:///c:/py_smartdocs/backend/apps/llm/llm_ocr/llm_ocr_factory.py) | Factory tạo OCR service instance |
| 🆕 | [llm/llm_ocr/mistral_ocr.py](file:///c:/py_smartdocs/backend/apps/llm/llm_ocr/mistral_ocr.py) | OCR qua Mistral API (PDF, ảnh, Word → Markdown) |
| 🆕 | [llm/llm_ocr/mistral_uploader.py](file:///c:/py_smartdocs/backend/apps/llm/llm_ocr/mistral_uploader.py) | Upload/download/delete file trên Mistral storage |

### Services — RAG Pipeline

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [services/rag_base/extract/extract_content_service.py](file:///c:/py_smartdocs/backend/apps/services/rag_base/extract/extract_content_service.py) | Trích xuất nội dung: dùng pypdf hoặc Mistral OCR |
| 🆕 | [services/rag_base/locate/faiss_service.py](file:///c:/py_smartdocs/backend/apps/services/rag_base/locate/faiss_service.py) | FAISS vector store service (skeleton, chưa implement) |
| 🆕 | [services/rag_base/locate/locate_service.py](file:///c:/py_smartdocs/backend/apps/services/rag_base/locate/locate_service.py) | Locate/retrieval service — kết nối embedding + vector search |
| 🆕 | [services/rag_base/locate/vector_store_base.py](file:///c:/py_smartdocs/backend/apps/services/rag_base/locate/vector_store_base.py) | Abstract base cho vector store implementations |
| 🆕 | [services/rag_base/storage/storage_service.py](file:///c:/py_smartdocs/backend/apps/services/rag_base/storage/storage_service.py) | File storage service: lưu file cục bộ, phân loại MIME |

### Services — Graph RAG

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [services/graph_rag/graph_service.py](file:///c:/py_smartdocs/backend/apps/services/graph_rag/graph_service.py) | Graph RAG service (skeleton) |

### Services — Chat (Django App)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [services/chat/models.py](file:///c:/py_smartdocs/backend/apps/services/chat/models.py) | Tạo class rỗng ban đầu |
| ✏️ | [services/chat/models.py](file:///c:/py_smartdocs/backend/apps/services/chat/models.py) | **(Chưa commit)** Triển khai Django ORM models: `ConversationModel`, `DocumentModel` (`faiss_index`), `ConversationFilesModel`, `MessageModel` — ánh xạ tới các bảng trong `structure.sql` |
| 🆕 | [services/chat/serializers.py](file:///c:/py_smartdocs/backend/apps/services/chat/serializers.py) | Tạo serializer class rỗng ban đầu |
| ✏️ | [services/chat/serializers.py](file:///c:/py_smartdocs/backend/apps/services/chat/serializers.py) | **(Chưa commit)** Triển khai DRF `ModelSerializer` cho `ConversationModel`, `MessageModel`, `DocumentModel` |
| 🆕 | [services/chat/urls.py](file:///c:/py_smartdocs/backend/apps/services/chat/urls.py) | URL routing cho chat app |
| 🆕 | [services/chat/views.py](file:///c:/py_smartdocs/backend/apps/services/chat/views.py) | ViewSet skeleton cho Conversation & Message |
| 🆕 | [services/chat/migrations/0001_initial.py](file:///c:/py_smartdocs/backend/apps/services/chat/migrations/0001_initial.py) | **(Chưa commit)** Django migration tạo bảng ban đầu |

### Application Layer

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [application/conversations/conversation.py](file:///c:/py_smartdocs/backend/apps/application/conversations/conversation.py) | Application service cho conversation logic |
| 🆕 | [application/messages/message.py](file:///c:/py_smartdocs/backend/apps/application/messages/message.py) | Application service cho message logic |

### Background Tasks

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [tasks/document_tasks.py](file:///c:/py_smartdocs/backend/apps/tasks/document_tasks.py) | Celery tasks cho document processing (skeleton) |
| 🆕 | [tasks/conversation_tasks.py](file:///c:/py_smartdocs/backend/apps/tasks/conversation_tasks.py) | Celery tasks cho conversation management (skeleton) |
| 🆕 | [job/job_manager.py](file:///c:/py_smartdocs/backend/apps/job/job_manager.py) | Job manager utility |

### Exceptions & Utils

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [exceptions/exceptions.py](file:///c:/py_smartdocs/backend/apps/exceptions/exceptions.py) | Custom exceptions cho toàn bộ backend |
| 🆕 | [utils/hash_content.py](file:///c:/py_smartdocs/backend/apps/utils/hash_content.py) | Hàm hash nội dung file |
| 🆕 | [utils/is_content_empty.py](file:///c:/py_smartdocs/backend/apps/utils/is_content_empty.py) | Kiểm tra nội dung rỗng |
| 🆕 | [utils/is_path_valiable.py](file:///c:/py_smartdocs/backend/apps/utils/is_path_valiable.py) | Kiểm tra đường dẫn hợp lệ |
| 🆕 | [utils/mime_type.py](file:///c:/py_smartdocs/backend/apps/utils/mime_type.py) | Xác định MIME type từ file |

---

## VI. FRONTEND — Shiny App

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🔄 | [frontend/app.py](file:///c:/py_smartdocs/frontend/app.py) | Đổi tên từ `frontend/index.py` → `frontend/app.py`. Tái cấu trúc layout: thêm sidebar phải, cải thiện mock mode, thêm reactive logic cho sessions & documents |
| ✏️ | [frontend/app.py](file:///c:/py_smartdocs/frontend/app.py) | **(Chưa commit)** Thêm logic Login/Signup modal, `user_badge`, `account_menu` output, xử lý exception khi render documents, thêm `account_dropdown_ui` |
| ✏️ | [frontend/assets/css/app.css](file:///c:/py_smartdocs/frontend/assets/css/app.css) | Mở rộng CSS đáng kể: thêm styles cho sidebar phải, session history, doc-selector, glassmorphism effects, responsive layout |
| ✏️ | [frontend/components/chat/message.py](file:///c:/py_smartdocs/frontend/components/chat/message.py) | Sửa logic mock mode, cải thiện metadata hiển thị |
| ✏️ | [frontend/components/chat/message.py](file:///c:/py_smartdocs/frontend/components/chat/message.py) | **(Chưa commit)** Thêm `update_conversation_documents()` khi gửi tin nhắn vào conversation đã tồn tại |
| ✏️ | [frontend/components/header.py](file:///c:/py_smartdocs/frontend/components/header.py) | Sửa layout header |
| ✏️ | [frontend/components/header.py](file:///c:/py_smartdocs/frontend/components/header.py) | **(Chưa commit)** Thêm `user_badge`, `account_menu` vào header, tạo hàm `account_dropdown_ui()` với logic hiển thị Login/Signup hoặc Logout |
| ✏️ | [frontend/components/history.py](file:///c:/py_smartdocs/frontend/components/history.py) | Cập nhật component hiển thị lịch sử hội thoại |
| ✏️ | [frontend/components/settings/model_settings.py](file:///c:/py_smartdocs/frontend/components/settings/model_settings.py) | Sửa nhỏ cấu hình model settings |
| ✏️ | [frontend/components/sidebars/left.py](file:///c:/py_smartdocs/frontend/components/sidebars/left.py) | Tái cấu trúc: chuyển sessions sang sidebar phải, giữ upload + documents |
| 🆕 | [frontend/components/sidebars/right.py](file:///c:/py_smartdocs/frontend/components/sidebars/right.py) | Sidebar phải mới — hiển thị danh sách sessions (history) |
| ✏️ | [frontend/components/upload_files.py](file:///c:/py_smartdocs/frontend/components/upload_files.py) | Cập nhật UI upload files |
| 🗑️ → 🆕 | [frontend/components/account/login.py](file:///c:/py_smartdocs/frontend/components/account/login.py) | Xoá phiên bản cũ (commit `5ef6c8d`), tạo lại **(chưa commit)** dưới dạng Shiny modal dialog |
| 🗑️ → 🆕 | [frontend/components/account/signup.py](file:///c:/py_smartdocs/frontend/components/account/signup.py) | Xoá phiên bản cũ (commit `5ef6c8d`), tạo lại **(chưa commit)** dưới dạng Shiny modal dialog |

### Frontend — Assets (JS/CSS/Images)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [assets/js/dropdown-close.js](file:///c:/py_smartdocs/frontend/assets/js/dropdown-close.js) | JS đóng dropdown khi click bên ngoài |
| 🆕 | [assets/js/model_settings.js](file:///c:/py_smartdocs/frontend/assets/js/model_settings.js) | JS điều khiển modal settings |
| 🆕 | [assets/js/upload/google-picker.js](file:///c:/py_smartdocs/frontend/assets/js/upload/google-picker.js) | JS tích hợp Google Picker API |
| 🆕 | [assets/js/upload/modal-upload.js](file:///c:/py_smartdocs/frontend/assets/js/upload/modal-upload.js) | JS cho modal upload |
| 🆕 | [assets/js/upload/sidebar-upload.js](file:///c:/py_smartdocs/frontend/assets/js/upload/sidebar-upload.js) | JS cho sidebar upload (drag & drop) |
| 🆕 | [assets/google-drive.png](file:///c:/py_smartdocs/frontend/assets/google-drive.png) | Icon Google Drive |
| 🆕 | [assets/monitor.png](file:///c:/py_smartdocs/frontend/assets/monitor.png) | Icon monitor |
| 🆕 | [assets/upload.png](file:///c:/py_smartdocs/frontend/assets/upload.png) | Icon upload |

---

## VII. SYS_SERVICES — Shared Services (Cross-cutting)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🔄 | [sys_services/api_client.py](file:///c:/py_smartdocs/sys_services/api_client.py) | Di chuyển từ `frontend/services/api_client.py` → `sys_services/`. Thêm httpx methods, refactor error handling |
| ✏️ | [sys_services/api_client.py](file:///c:/py_smartdocs/sys_services/api_client.py) | **(Chưa commit)** Thêm `update_conversation_documents()`, `login()`, `signup()` |
| 🆕 | [sys_services/logging.py](file:///c:/py_smartdocs/sys_services/logging.py) | Logging service (Singleton + DI pattern) |
| 🆕 | [sys_services/system_dirs.py](file:///c:/py_smartdocs/sys_services/system_dirs.py) | Định nghĩa thư mục hệ thống |
| 🆕 | [sys_services/time_counter.py](file:///c:/py_smartdocs/sys_services/time_counter.py) | Đo thời gian thực thi |

### Enums

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [enums/e_backend_storage_name.py](file:///c:/py_smartdocs/sys_services/enums/e_backend_storage_name.py) | Enum tên backend storage |
| 🆕 | [enums/e_mime_type.py](file:///c:/py_smartdocs/sys_services/enums/e_mime_type.py) | Enum MIME types hỗ trợ |
| 🆕 | [enums/e_provider_name.py](file:///c:/py_smartdocs/sys_services/enums/e_provider_name.py) | Enum tên LLM provider (gemini, mistral, ollama) |
| 🆕 | [enums/e_type_message.py](file:///c:/py_smartdocs/sys_services/enums/e_type_message.py) | Enum loại message (log level) |

### Config Readers

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [read_config/config_provider.py](file:///c:/py_smartdocs/sys_services/read_config/config_provider.py) | Config provider tổng hợp — đọc `.env` |
| 🆕 | [read_config/read_chunking_config.py](file:///c:/py_smartdocs/sys_services/read_config/read_chunking_config.py) | Đọc config chunking (chunk_size, overlap) |
| 🆕 | [read_config/read_gemini_config.py](file:///c:/py_smartdocs/sys_services/read_config/read_gemini_config.py) | Đọc Gemini API config |
| 🆕 | [read_config/read_google_config.py](file:///c:/py_smartdocs/sys_services/read_config/read_google_config.py) | Đọc Google Cloud / Picker config |
| 🆕 | [read_config/read_mistral_config.py](file:///c:/py_smartdocs/sys_services/read_config/read_mistral_config.py) | Đọc Mistral API config |
| 🆕 | [read_config/read_models.py](file:///c:/py_smartdocs/sys_services/read_config/read_models.py) | Đọc danh sách model khả dụng |
| 🆕 | [read_config/read_ollama_config.py](file:///c:/py_smartdocs/sys_services/read_config/read_ollama_config.py) | Đọc Ollama config (base URL, model) |
| 🆕 | [read_config/read_qdrant_config.py](file:///c:/py_smartdocs/sys_services/read_config/read_qdrant_config.py) | Đọc Qdrant vector DB config |

---

## VIII. TESTS

> Tất cả tests ban đầu nằm ở `frontend/tests/`, sau đó được di chuyển sang `tests/` (root level) ở commit `8a15dd7`.

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕🔄 | [tests/chunking_test.py](file:///c:/py_smartdocs/tests/chunking_test.py) | Test chunking pipeline |
| 🆕🔄 | [tests/embedding_test.py](file:///c:/py_smartdocs/tests/embedding_test.py) | Test embedding generation |
| 🆕🔄 | [tests/gemini_qdrant_test.py](file:///c:/py_smartdocs/tests/gemini_qdrant_test.py) | Test pipeline Gemini + Qdrant |
| 🆕🔄 | [tests/llm_test.py](file:///c:/py_smartdocs/tests/llm_test.py) | Test kết nối LLM clients |
| 🆕🔄 | [tests/mistral_faiss_test.py](file:///c:/py_smartdocs/tests/mistral_faiss_test.py) | Test pipeline Mistral + FAISS |
| 🆕🔄 | [tests/mistral_ocr_core_test.py](file:///c:/py_smartdocs/tests/mistral_ocr_core_test.py) | Test core OCR processing |
| 🆕🔄 | [tests/mistral_ocr_image_test.py](file:///c:/py_smartdocs/tests/mistral_ocr_image_test.py) | Test OCR trên ảnh |
| 🆕🔄 | [tests/mistral_ocr_normalize_pipeline_test.py](file:///c:/py_smartdocs/tests/mistral_ocr_normalize_pipeline_test.py) | Test pipeline OCR → Normalize |
| 🆕🔄 | [tests/mistral_ocr_test.py](file:///c:/py_smartdocs/tests/mistral_ocr_test.py) | Test Mistral OCR đầy đủ |
| 🆕🔄 | [tests/normalize_test.py](file:///c:/py_smartdocs/tests/normalize_test.py) | Test normalize text |
| 🆕🔄 | [tests/traditional_extract_text_test.py](file:///c:/py_smartdocs/tests/traditional_extract_text_test.py) | Test trích xuất text truyền thống (pypdf) |

---

## IX. DOCUMENTATION

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [README.md](file:///c:/py_smartdocs/README.md) | Hướng dẫn cài đặt và chạy dự án |
| 🆕 | [TODOS.md](file:///c:/py_smartdocs/TODOS.md) | Danh sách TODO |
| 🆕 | [PROJECT_STATUS.md](file:///c:/py_smartdocs/PROJECT_STATUS.md) | **(Chưa commit)** Báo cáo chi tiết trạng thái dự án |
| 🆕 | [.env.example](file:///c:/py_smartdocs/.env.example) | Template biến môi trường |
| ✏️ | [.gitignore](file:///c:/py_smartdocs/.gitignore) | Cập nhật ignore rules |
| ✏️ | [backend/requirements/base.txt](file:///c:/py_smartdocs/backend/requirements/base.txt) | Thêm dependencies mới |
| ✏️ | [frontend/requirements/dev.txt](file:///c:/py_smartdocs/frontend/requirements/dev.txt) | Thêm dependencies cho dev |

### Docs — Backend

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [docs/backend/_project_overview.md](file:///c:/py_smartdocs/docs/backend/_project_overview.md) | Tổng quan kiến trúc backend (636 dòng) |
| ✏️ | [docs/backend/chat.md](file:///c:/py_smartdocs/docs/backend/chat.md) | Cập nhật doc chat module |
| ✏️ | [docs/backend/core.md](file:///c:/py_smartdocs/docs/backend/core.md) | Mở rộng doc core module |
| 🆕 | [docs/backend/debug.md](file:///c:/py_smartdocs/docs/backend/debug.md) | Hướng dẫn debug |
| ✏️ | [docs/backend/documents.md](file:///c:/py_smartdocs/docs/backend/documents.md) | Cập nhật doc documents |
| ✏️ | [docs/backend/jobs.md](file:///c:/py_smartdocs/docs/backend/jobs.md) | Cập nhật doc jobs |
| ✏️ | [docs/backend/llm.md](file:///c:/py_smartdocs/docs/backend/llm.md) | Cập nhật doc LLM |
| 🆕 | [docs/backend/pipeline/traditional_pipeline.md](file:///c:/py_smartdocs/docs/backend/pipeline/traditional_pipeline.md) | Doc pipeline truyền thống |
| 🗑️ | docs/backend/retrieval.md | Xoá — nội dung đã merge vào các file khác |
| 🆕 | [docs/backend/route.md](file:///c:/py_smartdocs/docs/backend/route.md) | Doc API routing |
| 🆕 | [docs/backend/share.md](file:///c:/py_smartdocs/docs/backend/share.md) | Doc shared components |

### Docs — Frontend & Research

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| ✏️ | [docs/frontend/frontend.md](file:///c:/py_smartdocs/docs/frontend/frontend.md) | Cập nhật doc frontend |
| 🆕 | [docs/research_docs.md](file:///c:/py_smartdocs/docs/research_docs.md) | Links tài liệu nghiên cứu (RAG, LLM, Vector DB) |

### Docs — SQL & Assignment

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | [docs/sql/structure.sql](file:///c:/py_smartdocs/docs/sql/structure.sql) | Schema SQL cho MariaDB: bảng `conversation`, `faiss_index`, `conversation_files`, `messages` |
| 🆕 | [docs/Asignment.docx](file:///c:/py_smartdocs/docs/Asignment.docx) | File bài tập/đề tài |

---

## X. FILES ĐÃ XOÁ

| File | Lý do |
|------|-------|
| `docs/backend/retrieval.md` | Nội dung đã được merge vào các doc khác |
| `frontend/components/account/login.py` | Xoá ở commit `5ef6c8d`, tạo lại (chưa commit) dưới dạng modal |
| `frontend/components/account/signup.py` | Xoá ở commit `5ef6c8d`, tạo lại (chưa commit) dưới dạng modal |
| `frontend/index.py` | Đổi tên thành `frontend/app.py` |
| `frontend/services/api_client.py` | Di chuyển sang `sys_services/api_client.py` |

---

## XI. DATA FILES (Chưa commit)

| Trạng thái | File | Mô tả |
|:---:|------|-------|
| 🆕 | `db.sqlite3` | SQLite database (dùng cho dev thay MariaDB) |
| 🆕 | `storage/media/*.docx, *.pdf, *.txt` | Các file tài liệu đã upload thử qua API |

---

## XII. THỐNG KÊ TỔNG HỢP

| Hạng mục | Số lượng |
|----------|:--------:|
| **Files thêm mới** | ~100 |
| **Files chỉnh sửa** (đã commit) | 17 |
| **Files chỉnh sửa** (chưa commit) | 8 |
| **Files xoá** | 3 |
| **Files đổi tên/di chuyển** | 2 + 11 tests |
| **Tổng commits** | 33 |
| **Dòng code thêm** | ~5,732 |
| **Dòng code xoá** | ~412 |

---

## XIII. LỊCH SỬ COMMIT (Chronological)

| # | Hash | Mô tả |
|:-:|:----:|-------|
| 1 | `35d2237` | First commit — tạo base frontend (Shiny) |
| 2 | `f7dc9c7` | Style buttons trên chat bar |
| 3 | `185de19` | Xoá form upload cũ |
| 4 | `ecf398d` | Thử nghiệm Google Picker API |
| 5 | `fc2bfc7` | Thêm event click dropdown |
| 6 | `5ef6c8d` | Xoá login/signup, tạo test files |
| 7 | `b8d3cf7` | Thêm README hướng dẫn cài đặt |
| 8 | `5791fcd` | Di chuyển services → sys_services, thêm logging |
| 9 | `7b04914` | Chuyển sang module type (`python3 -m`), tạo chunking files |
| 10 | `a0288c2` | Test embedding + locating (Gemini+Qdrant, Mistral+FAISS) |
| 11 | `cfcebb7` | Cập nhật docs backend |
| 12 | `6a60376` | Thêm links research docs |
| 13 | `ca927fb` | Thêm links research docs |
| 14 | `e8066d6` | Tạo cấu trúc base — IoC pattern |
| 15 | `df3f689` | Tạo base/prototype files |
| 16 | `f2fe812` | Chỉnh interfaces cho LLM, tạo test LLM |
| 17 | `cc1fcd6` | Logging (Singleton+DI), thêm Ollama support |
| 18 | `79f18aa` | Refactor tên interface theo convention |
| 19 | `738dbc8` | Refactor tên enum files |
| 20 | `eba6d8a` | Tạo `mistral_uploader.py`, util files, cải thiện logging |
| 21 | `0276c47` | Hoàn thiện `storage.py`, thêm load/delete file |
| 22 | `8029298` | Di chuyển file_storage → core |
| 23 | `790c1a3` | Migrate backend structure, đổi tên theo Python conventions |
| 24 | `bb067bf` | Migrate structure, tạo interface normalize |
| 25 | `72b403b` | Migrate interfaces, xoá code Mistral OCR thừa |
| 26 | `6766fa3` | Xoá thư mục không dùng |
| 27 | `2d17892` | Cập nhật test files |
| 28 | `0402ca4` | Migrate interfaces, tạo schema MariaDB, tách core/services |
| 29 | `b80133d` | Chuyển async → sync (jobs/ xử lý background) |
| 30 | `a4fc0d2` | Sửa params logger trên `__init__` |
| 31 | `6c1e5ec` | Test model LLM |
| 32 | `8a6e3ed` | Dùng test file với real context |
| 33 | `7596c95` | Migrate `i_completion` → `i_dataclass_transaction` |
| 34 | `8a15dd7` | Chuyển sessions sang sidebar phải, di chuyển tests/ |
| — | *(uncommitted)* | Django setup, ORM models, API implementations, Auth, Login/Signup modals |
