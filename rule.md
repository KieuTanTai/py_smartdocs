# SmartDocs AI – Quy tắc & Kiến trúc dự án

> Đọc tài liệu này **trước khi** thêm tính năng mới hoặc chỉnh sửa code, để đảm bảo nhất quán với kiến trúc và các quyết định kỹ thuật đã thống nhất.

---

## 1. Kiến trúc & cấu trúc thư mục

Luồng layer: `api/` → `apps/application/` → `apps/jobs/` → `apps/tasks/` → `core/`, `llm/`, `services/`

- **`api/`**: theo cấu trúc Django URL, chỉ validate lớp 1 rồi gọi `application/`.
- **`apps/application/`**: validate nghiệp vụ, chuẩn bị dữ liệu, handle exception, gọi `job_manager` để chạy job nền, gọi flush log sau khi xong.
- **`apps/jobs/`**: chia theo nghiệp vụ (upload, message, conversation, delete...). `job_manager` là factory gọi các job nhỏ.
- **`apps/tasks/`**: các bước nhỏ trong 1 job. Job `upload` gọi flow: `extract → normalize → chunking + save cache + generate ids → embed → save`.
- **`core/interfaces/`**: interface dùng cho core, services, `llm/`.
- **`core/enums/`**: enum dùng chung.
- **`core/`**: chứa dataclass request/response dùng chung toàn dự án (model nên gom vào 1 folder riêng dạng `model/` nếu refactor).
- **`interfaces/`** (ngoài `core/`): dùng cho jobs, tasks, application — tương tác cả service lẫn core.
- **`llm/`**: client cho từng provider LLM (Mistral, Gemini, Ollama).
- **`services/`**: business service (FAISS, BM25, Redis cache, Neo4j...). Hybrid search nằm ở `services/rag_base/search`.
- **`sys_services/`**: service hệ thống (logging, ssl_fix...).
- **`metadata/`**: lưu file input của user + metadata FAISS ghi xuống.
- **`utils/`**: viết dạng function thường là được, không bắt buộc class.
- Không tin tưởng các file `.md` cũ trong `docs/` do AI tạo từ project trước — đặc biệt **`docs/pipeline/traditional_pipeline.md` từng ghi SAI thứ tự pipeline** (đã sửa, xem mục 4).
- Log ghi ra `docs/logs/`, mỗi ngày chạy 1 folder riêng.

---

## 2. Quy tắc code bắt buộc (IoC / DI / SOLID)

- Mọi class **phải có ít nhất 1 interface**, prefix `I_` (vd `ILogger`, `IUpload`), viết ra file riêng.
- Mọi instance (logger, service, client...) **do container quản lý và inject** — không tự tạo instance trong method/class, không import giữa method (import để hết đầu file).
- **Không sửa interface đã có.** Nếu cần method mới mà không tương thích interface cũ → tạo interface mới (tránh phá class khác đang dùng interface cũ). Nếu có 2 interface cùng mục đích khác cách triển khai, tạo 1 interface trung gian, `locate_factory` trả về interface trung gian đó.
- Single Responsibility: mỗi `def` chỉ làm 1 việc; logic dài → tách helper `def` riêng.
- **Không dùng `Dict[str, Any]`** cho dữ liệu có cấu trúc — luôn tạo dataclass riêng.
- Return type của high-level class phụ thuộc vào return type của low-level class mà nó gọi — không tự ý đổi cấu trúc dữ liệu giữa chừng.
- Log lỗi hệ thống **không** dùng encoding UTF-8 (khác với log thường).
- Mọi config liên quan `.env`/secret phải để trong `.env`, không hardcode trong source.
- Dự án hiện chạy **HTTP**, không cần SSL/CA config — không tự thêm `ssl_config`.

---

## 3. Quy ước ID & Hashing

- **Phải normalize text trước khi hash.** Quên bước này → 2 nội dung giống hệt nhau chỉ lệch khoảng trắng sẽ ra hash khác nhau → trùng lặp/sai dữ liệu.
- ID hash dùng cho FAISS = **hash của embedding từng chunk**, không phải hash của `file_id`.
- FAISS chỉ nhận `ids` kiểu **int64** — phải convert hash/UUID sang int64 trước khi đưa vào FAISS.
- `vector_id` của FAISS = nối các `document_id` bằng dấu `_` (vd `12234_64300`) — đại diện FAISS metadata cho nhiều file cùng lúc.
- ID từng chunk: dạng `file_id:chunk_index`.
- Ưu tiên dùng **UUID** thay vì hexdigest cho các loại ID khác (faiss_file_id, bm25 file id...).

---

## 4. Pipeline xử lý tài liệu (Upload)

- **Bắt buộc dùng OCR (Mistral)** để extract — không dùng `Document` parser thường (OCR đọc được cả file docs lẫn image).
- Extract dùng chung **1 method `extract()`**, trả về object đầy đủ metadata (`OCRResponse`: có field `id`, `pages`...), không tách riêng hàm cho text vs OCR.
- Trước khi extract, phải **upload file lên cloud Mistral qua `ILLMUploader`** để lấy `file_id` (`ICreateFileResponse`). Chỉ Mistral có upload, Ollama không có.
- Flow chuẩn: `extract → normalize → chunk → cache (chỉ cache sau khi có embed) → embed → save`.
- Upload nhiều file: **loop xử lý từng file ở task** (không loop trong job). Sau đó dùng `np.vstack` gộp toàn bộ embedding của các file thành 1 khối + gộp ids tương ứng thành 1 `np.ndarray` duy nhất.
- Flow tạo conversation: **tạo conversation trước, rồi mới process file** (không phải process xong mới tạo).
- Upload fail → xóa (remove) conversation vừa tạo.
- Giới hạn FE: tối đa **3 file/lần upload**.
- Sau upload thành công, hệ thống tự tạo 1 message **summarize** toàn bộ nội dung file vừa upload, gửi vào conversation mới tạo → vừa dùng làm tiêu đề vừa làm tóm tắt tổng thể.

---

## 5. FAISS / Vector search

- Đã thử **Qdrant nhưng bỏ** vì lệch số chiều embedding (Mistral embed ra 1024 chiều, gói free Qdrant chỉ hỗ trợ 512/1536/3072) → chốt dùng **FAISS**.
- FAISS lưu vector **trên RAM**, không trên disk → cần SQLite lưu metadata (path, conversation) để biết load lại gì khi cần.
- FAISS storage **không phải singleton** → cần 1 class singleton riêng cache giá trị sau khi FAISS ghi metadata, để dễ xử lý multithread.
- Không index theo từng file riêng (tốn CPU/RAM khi build lại index mỗi lần) — **vstack toàn bộ embedding** của tất cả file thành 1 khối, dùng ids để filter theo target file lúc search.
- FAISS service hiện ở dạng factory — cần giữ lại index sau khi tạo (tránh mỗi message phải đọc lại file persist từ đầu).
- Search flow: user chọn file → dùng id file tìm trong cache (Redis) ra vector → FAISS search. Cache miss → load từ `metadata/` lên rồi lưu lại vào cache.
- BM25: param có thể để rỗng → nếu rỗng, fallback search thẳng trên FAISS (phòng case BM25 lỗi).
- Chunk size: cân nhắc tăng lên **2000** (1000 với file dài dễ gây peak request).

---

## 6. Redis cache

- Cấu trúc: `key = file_id`, `value = list các {index, text_value, embedding}`.
- **Không** cache kết quả embed thô — cache chunk + id từng chunk kèm embedding (để tra ngược raw text từ FAISS indices khi cần, vd cho summarize).
- Việc cache phải **đợi embed xong mới cache**.

---

## 7. LLM & Embedding

- 3 model: **Mistral AI**, **Gemini**, **Ollama** (self-host, bản `qwen2.5:1.5b-instruct`).
- `model_name` (str, lấy từ FE/`.env`) **khác** `provider` (enum `EProviderName`) — phải lấy đúng `model_name` để chọn embedder/client tương ứng, không chỉ dựa vào provider.
- Embed trả về object `IEmbeddingResponse`: gồm `embed_contents`, `dimension`, `shape`.
- Generate trả về object `IGenerateResponse`: tối thiểu có `message`, `model_name`; các field còn lại optional (Gemini không lấy được nhiều metadata).

---

## 8. Graph RAG (Neo4j)

- Dùng **Neo4j cloud cluster**.
- Cần dùng LLM generate ra **relationship** trước khi đưa vào Neo4j (bước graph extraction), chưa rõ flow chi tiết — cần tìm hiểu thêm khi tiếp tục.
- Nếu set `from_pdf=True`, Neo4j dùng tool extract riêng của nó → **không dùng được OCR** → phải set `from_pdf=False` khi cần OCR.
- `llm/` cần có method riêng lấy instance embedder/llm client đúng **interface của Neo4j** (khác interface custom của project) — Neo4j tự build/run instance đó, project chỉ cần cung cấp.
- Model lite chạy được nhưng chất lượng entities/relationship chưa rõ, cần test thêm. Model lớn hơn cần tối thiểu **6GB VRAM**.
- Graph RAG **chậm hơn** base RAG — chấp nhận đánh đổi tốc độ lấy ngữ cảnh/độ chính xác.
- `create_index` của Neo4j hiện còn lỗi (tạo cái đầu được, các lần sau bị tạch) — cần fix khi quay lại phần này.

---

## 9. Database (SQLite/Django)

- DB hiện dùng **SQLite của Django** (đã tạm dừng module MariaDB để tập trung phần lõi).
- Model `Document` đại diện cho FAISS, quan hệ **1-1 với Conversation** (1 conversation chỉ có 1 file FAISS).
- Model `conversation_file`: chỉ giữ `cloud_id` (id file trên cloud Mistral), quan hệ **1-N với Conversation**. Không lưu object file trong DB vì file nằm trên cloud.
- `conversation_id`: UUID v7.
- `conversation_name`: dùng riêng để đặt tên file FAISS (string nối bằng `_`), **khác** với `conversation_id`.
- `status` của document: dùng enum riêng, không dùng string thường.
- DB chỉ động tới khi **xóa conversation** (xóa sạch cả message, file, mapping liên quan) — không có chức năng xóa riêng lẻ từng file/message.

---

## 10. Logging & Time tracking

- Logger inject qua container, **không tự tạo instance logger riêng** trong class (đã singleton sẵn).
- **Log Pool**: gom log vào pool thay vì mở/đóng I/O mỗi lần log → giảm tải CPU, đánh đổi bằng RAM. Quy ước: **chỉ flush ở class cấp cao nhất** (`application`/`api`).
- Log Pool chạy multithread → cần khóa (lock) để tránh deadlock khi nhiều thread cùng ghi/flush.
- `ITimeCounter` kiểu stopwatch: gọi `start()` 1 lần, các lần sau gọi `stop()`/`get_elapsed_time()` (tự động stop bên trong `get_elapsed_time()`), không cần start lại.
- Mapping của `ITimeCounter`/`TimeCounter` để public, dễ mở rộng field khi cần (có sẵn `IRetrievalTimeCounterResponse`, thiếu field gì thì bổ sung trực tiếp).

---

## 11. Concurrency

- Message pipeline: chạy **đa luồng** cho BM25 và FAISS search song song; tránh nạp toàn bộ file lớn vào List để đỡ ngốn RAM.
- Delete job: dùng `async_to_sync` (từ `asgiref`) thay vì `asyncio.run()` để tránh hỏng event loop khi chạy đa luồng xóa BM25 + FAISS.

---

## 12. Package & dependency cần lưu ý

- Đã gỡ (gây conflict với `mistralai`): `opentelemetry-exporter-otlp-proto-http`, `mistralai` (bản cũ), `neo4j-graphrag[mistralai]`, `opentelemetry-sdk`.
- Cài lại `mistralai` sau khi gỡ các package trên.

---

## 13. Field contract API (BE ↔ FE)

- **Upload tài liệu** → trả về: `id`, `title`, `status`.
- **Tạo/lấy hội thoại (conversation)** → trả về: `conversation_id`, `status`, `date_create`.
- **Gửi tin nhắn (message)** → trả về: nội dung trả lời của assistant, `used_mock` (có dùng mock data hay không), `conversation_id`.
- FE gửi `provider` = `EProviderName.value`, `model_name` = giá trị text người dùng chọn.
- FE gửi loại pipeline: `normal` (base RAG) hoặc `graph` (graph RAG).

---

## 14. Đã loại bỏ khỏi scope (không implement lại)

- Login/signup (chỉ dựng khung UI cho đẹp, không có logic thật).
- Circuit breaker (chưa implement).
- HTTPS/SSL config (`ssl_config`, CA bundle) — dự án chạy HTTP thuần.