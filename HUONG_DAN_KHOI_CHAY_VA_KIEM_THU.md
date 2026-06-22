# HƯỚNG DẪN KHỞI CHẠY VÀ KIỂM THỬ DỰ ÁN SMARTDOCS AI

Tài liệu này hướng dẫn chi tiết cách thiết lập môi trường, chạy ứng dụng thực tế và cách thực thi các kịch bản kiểm thử (Test Cases) từ đơn lẻ đến toàn diện, cũng như cách xem kết quả dữ liệu trả về từ API.

---

## 1. KHỞI CHẠY DỰ ÁN (SETUP & RUN PROJECT)

Dự án gồm hai phần chính: **Backend** (Django REST Framework) và **Frontend** (Shiny for Python), phối hợp qua REST API và Celery background worker.

### 1.1. Chuẩn Bị Môi Trường & Thư Viện

#### Bước 1: Tạo và kích hoạt môi trường ảo Python
```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac:
python3 -m venv .venv
source .venv/bin/activate
```

#### Bước 2: Cài đặt dependencies cho cả Backend và Frontend
```bash
# Cài đặt thư viện Backend
pip install -r backend/requirements/dev.txt

# Cài đặt thư viện Frontend
pip install -r frontend/requirements/dev.txt
```
*Lưu ý:* Phải cài đặt thêm thư viện `faiss` phù hợp với phần cứng:
```bash
# Bản chạy trên CPU (Khuyên dùng cho máy cá nhân / test nhanh)
pip install faiss-cpu

# Bản chạy trên GPU (Yêu cầu cài đặt CUDA và dùng Conda)
# conda install -c pytorch faiss-gpu
```

#### Bước 3: Cấu hình biến môi trường `.env`
Sao chép file `.env.example` thành `.env` và điền đầy đủ các thông tin API Key:
```bash
cp .env.example .env
```
*Các biến quan trọng:*
*   `GEMINI_API_KEY`: API key của Google để chạy mô hình Gemini Flash & Gemini Embedding.
*   `MISTRAL_API_KEY`: API key của Mistral (yêu cầu để chạy OCR trích xuất file scan).
*   `SECRET_KEY`: Khóa bảo mật của Django.
*   `DB_ENGINE`: Mặc định dùng `django.db.backends.sqlite3` để kiểm thử cục bộ.

#### Bước 4: Tạo cơ sở dữ liệu Django (Migration)
```bash
python manage.py migrate
```

---

### 1.2. Khởi Chạy Các Thành Phần Trong Chế Độ Development

Để chạy toàn bộ dự án trên máy cục bộ, bạn cần mở các Terminal riêng biệt để chạy các tiến trình sau:

#### Terminal 1: Khởi chạy Django Backend Server (Port 8000)
```bash
python manage.py runserver
```

#### Terminal 2: Khởi chạy Shiny Frontend Web UI (Port 8001)
```bash
shiny run --app-dir frontend --reload --port 8001
```
*Truy cập giao diện tại:* http://localhost:8001

#### Terminal 3: Khởi chạy Redis Server (Yêu cầu cài đặt Redis local hoặc qua Docker)
Celery worker và cache của hệ thống cần Redis làm Message Broker:
```bash
# Chạy Redis qua Docker nhanh chóng:
docker run -d -p 6379:6379 redis:alpine
```

#### Terminal 4: Khởi chạy Celery Worker xử lý tác vụ nền
```bash
celery -A backend.apps.tasks worker --loglevel=info
```

#### Terminal 5: Khởi chạy Celery Beat điều phối scheduler (Tùy chọn)
```bash
celery -A backend.apps.tasks beat --loglevel=info
```

---

### 1.3. Khởi Chạy Bằng Docker Compose (Chế độ Production)
Nếu không muốn chạy thủ công từng terminal, bạn có thể khởi chạy toàn bộ stack dịch vụ thông qua Docker Compose:
```bash
docker compose -f docker-compose.yml --env-file .env up --build -d
```
Docker sẽ tự động kích hoạt 5 containers: `backend`, `frontend`, `redis`, `celery`, và `celery-beat`.

---

## 2. CHẠY KIỂM THỬ RIÊNG LẺ (RUN INDIVIDUAL TESTS)

Dự án cung cấp hệ thống unit tests viết bằng `pytest` để kiểm tra hoạt động độc lập của từng module dịch vụ.

### 2.1. Kiểm Thử Unit Test Đơn Giản
Chạy các bài test cô lập không phụ thuộc vào API mạng hoặc DB:

```bash
# Test bộ chuẩn hóa văn bản
pytest tests/normalize_test.py

# Test bộ chia nhỏ câu và văn bản
pytest tests/chunking_test.py

# Test hoạt động của bộ tích tụ log (LogPool)
pytest tests/log_pool_test.py
```

### 2.2. Kiểm Thử Tích Hợp Jobs Giả Lập (Mock Test)
Để kiểm tra tính nhất quán của luồng RAG và Graph RAG mà không cần gọi API Google/Mistral hay ghi DB thật, bạn sử dụng tệp kiểm thử [test_rag_jobs.py](file:///c:/py_smartdocs/tests/test_rag_jobs.py):
```bash
pytest tests/test_rag_jobs.py
```

### 2.3. Chạy Một Test Case Cụ Thể Trong Tệp
Sử dụng tham số `-k` kèm tên hàm test:
```bash
pytest tests/test_rag_jobs.py -k "test_upload_job_step_build_knowledge_graph"
```

### 2.4. Chạy Test Dạng Script Độc Lập
Một số tệp kiểm thử được thiết kế dưới dạng tập lệnh Python có hàm `__main__` để chạy trực tiếp:
```bash
python tests/embedding_test.py
python tests/llm_test.py
```

---

## 3. CHẠY KIỂM THỬ TOÀN BỘ (RUN ALL TESTS)

Có hai cách để quét và kiểm thử toàn bộ hệ thống:

### 3.1. Kiểm Thử Toàn Bộ Unit Test Bằng Pytest
Quét và thực thi tất cả các file test khớp cấu trúc trong thư mục `tests/`:
```bash
pytest
```
*Nếu muốn xem chi tiết thông tin log lúc chạy:*
```bash
pytest -v
```

### 3.2. Chạy Bộ Kiểm Thử Tích Hợp Hệ Thống Qua API (Comprehensive Integration Tests)
Tệp [comprehensive_test.py](file:///c:/py_smartdocs/tests/comprehensive_test.py) thực hiện giả lập Client gửi request HTTP thực tế tới server backend đang chạy để kiểm tra toàn diện các API.

**Yêu cầu:** Server backend (`python manage.py runserver`) phải đang chạy.

```bash
# Chạy thông qua công cụ quản lý test của Django:
python tests/run_comprehensive.py

# Hoặc chạy trực tiếp tệp script:
python -c "exec(open('tests/comprehensive_test.py').read())"
```

---

## 4. CHẠY KIỂM THỬ XEM DỮ LIỆU TRẢ VỀ (INSPECT TEST DATA OUTPUT)

Để đánh giá chất lượng câu trả lời hoặc xem cấu trúc JSON trả về của từng API khi chạy kiểm thử, bạn thực hiện theo các cách sau:

### 4.1. Hiển Thị Print/Stdout Lên Console Khi Chạy Pytest
Mặc định `pytest` sẽ nuốt (capture) toàn bộ câu lệnh `print` trong code test. Để buộc hiển thị dữ liệu trả về lên màn hình console, sử dụng cờ `-s`:
```bash
pytest -s tests/embedding_test.py
```
*Kết quả:* Bạn sẽ nhìn thấy cấu trúc mảng vector embedding thực tế trả về từ API Gemini hiển thị trực tiếp trên terminal.

### 4.2. Chạy Script Tích Hợp Frontend-Backend Có Xuất Dữ Liệu
Dự án có tệp [mock_frontend_backend_test.py](file:///c:/py_smartdocs/tests/mock_frontend_backend_test.py) giả lập chính xác hành vi gọi API từ Shiny Frontend qua class `ApiClient` tới Django API.

**Yêu cầu:** Khởi chạy Backend server trước.

```bash
# Chạy kiểm thử toàn bộ luồng và xem thông số
python -m tests.mock_frontend_backend_test
```
*Xem dữ liệu trả về theo từng phần độc lập:*
```bash
# Chỉ chạy và xem kết quả gọi API Health check
python -m tests.mock_frontend_backend_test --flow health

# Xem dữ liệu trả về của API Upload và Index tài liệu
python -m tests.mock_frontend_backend_test --flow documents

# Xem dữ liệu trả về của API tạo hội thoại
python -m tests.mock_frontend_backend_test --flow conversations

# Xem dữ liệu RAG và câu trả lời kèm thông số timing chi tiết
python -m tests.mock_frontend_backend_test --flow messages
```

#### Nơi lưu trữ dữ liệu trả về sau khi chạy:
Tệp kiểm thử này sẽ tự động tạo thư mục `tests/output/` và ghi đè báo cáo chi tiết kèm toàn bộ JSON response của các bước kiểm thử vào file:
*   [mock_test_results.txt](file:///c:/py_smartdocs/tests/output/mock_test_results.txt)

---

### 4.3. Theo Dõi Log Hệ Thống (System Logs)
Dự án lưu log chi tiết cho từng ngày xử lý. Để xem các lỗi phát sinh hoặc dữ liệu nội bộ được xử lý qua các service, bạn có thể kiểm tra tệp log được sinh ra tại:
*   `docs/logs/YYYY-MM-DD/` (Thư mục log phân theo ngày)
*   [upload_test_output.log](file:///c:/py_smartdocs/tests/upload_test_output.log) (Log ghi nhận tiến trình test upload)
