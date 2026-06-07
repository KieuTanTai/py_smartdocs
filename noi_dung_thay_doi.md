# Báo cáo Nội dung Thay đổi & Cập nhật Hệ thống

Tài liệu này tổng hợp toàn bộ các nội dung đã được sửa đổi, khắc phục lỗi và thêm mới trong hệ thống để thực hiện luồng tích hợp giả lập (mock pipeline) và sửa đổi các file test lỗi.

---

## 1. Khắc phục Lỗi Hệ thống & Sửa các File Test Cũ

### 🛠️ Sửa lỗi Encoding Log trên Windows
*   **File sửa đổi:** [sys_services/logging.py](file:///c:/py_smartdocs/sys_services/logging.py)
*   **Chi tiết:** Trên hệ điều hành Windows, việc ghi log chứa các ký tự Unicode (tiếng Việt, emoji) mặc định sử dụng bảng mã hệ thống (CP1252) dẫn đến lỗi crash `'charmap' codec can't encode characters`. Chúng tôi đã cấu hình hàm mở file log ghi đè cụ thể bằng `encoding="utf-8"`, giúp hệ thống ghi log tiếng Việt an toàn và ổn định.

### 🧪 Sửa file test [mistral_ocr_core_test.py](file:///c:/py_smartdocs/tests/mistral_ocr_core_test.py)
*   **Chi tiết:**
    *   Sửa lỗi import sai lớp `FileStorage` thành `FileStorageService` từ `storage_service.py`.
    *   Cập nhật lại cách khởi tạo tham số constructor cho phù hợp với backend thực tế (loại bỏ tham số `factory` dư thừa trong `FileStorageService` và tham số `provider` dư thừa trong `ExtractContentService`).
    *   Viết thêm một class wrapper `Extractor` cục bộ kế thừa giao diện cũ để tương thích với phương thức async `ocr.extract(file_path)` trong kịch bản test.

### 🧪 Sửa file test [mistral_ocr_normalize_pipeline_test.py](file:///c:/py_smartdocs/tests/mistral_ocr_normalize_pipeline_test.py)
*   **Chi tiết:**
    *   Thay thế các import cũ không tồn tại bằng các lớp thực tế của backend bao gồm: `MistralUploader`, `FileStorageService`, `ExtractContentService`, `Normalize`, và `Chunker`.
    *   Điều chỉnh logic xử lý kết quả OCR trích xuất trả về dạng chuỗi `str` trực tiếp thay vì bọc trong `ICompletionResponse.content`.

---

## 2. Tạo Kịch bản Tích hợp Giả lập Mới (New Mock Pipeline)

Chúng tôi đã viết mới file test tích hợp toàn diện: [tests/mock_pipeline_test.py](file:///c:/py_smartdocs/tests/mock_pipeline_test.py) để hiện thực hóa các yêu cầu thảo luận trong nhóm phát triển:

*   **Luồng xử lý (Upload - Storage - Scan OCR - Normalize - Hashing):**
    1.  **Upload & Storage:** Thực hiện lưu file tạm vào thư mục lưu trữ backend thông qua `FileStorageService`.
    2.  **Scan OCR:** Mô phỏng trích xuất OCR của Mistral. Chúng tôi đã dùng `unittest.mock` để giả lập (mock) phản hồi API của Mistral, cho phép chạy test thành công 100% kể cả khi không kết nối mạng hoặc không có API key.
    3.  **Normalize:** Chuẩn hóa chuỗi văn bản trích xuất bằng lớp `Normalize` của hệ thống.
    4.  **Hashing:** Tạo mã băm SHA-256 từ nội dung đã chuẩn hóa và **in trực tiếp ra màn hình console** để tiện giám sát.
*   **Mô phỏng Conversation Stack (LIFO):**
    *   Tự động sinh ra tên hội thoại kết hợp với ngày giờ hiện tại: `Tên hội thoại - YYYY-MM-DD HH:MM:SS`.
    *   Triển khai cấu trúc dữ liệu Stack để đẩy (push) các hội thoại mới lên trên cùng, sắp xếp theo thời gian tạo mới nhất.
*   **Ghi mã Hash vào Khung Chat:**
    *   Khởi tạo tin nhắn hệ thống (bootstrap message) chứa mã băm SHA-256 của tài liệu và ghi trực tiếp vào cơ sở dữ liệu hội thoại (`MessageModel`).
*   **Xác thực Log:**
    *   Tự động kiểm tra file log được sinh ra tại `docs/logs/YYYY-MM-DD/YYYY-MM-DD.log` và in 12 dòng log cuối cùng lên console để chứng minh các class backend thực tế đã ghi log thành công.

---

## 3. Nâng cấp API Gateway phía Backend

*   **File cập nhật:** [backend/api/gateway.py](file:///c:/py_smartdocs/backend/api/gateway.py)
*   **Nội dung nâng cấp:**
    *   Khi Frontend gửi yêu cầu tạo cuộc hội thoại mới (`POST /api/conversations/`), tiêu đề cuộc hội thoại sẽ tự động được nối thêm ngày giờ tạo (`- YYYY-MM-DD HH:MM:SS`).
    *   Nếu cuộc hội thoại được đính kèm tài liệu, hệ thống sẽ tự động tính toán mã băm SHA-256 của các tài liệu đó và hiển thị trực tiếp mã băm này trong tin nhắn chào mừng (bootstrap message) của khung chat.
    *   Hội thoại được tự động sắp xếp theo thứ tự mới nhất lên trước (`-conversation_created_at`), tương tự cơ chế Stack.

---

## 4. Hướng dẫn Chạy Kiểm thử (Test Commands)

### 1️⃣ Chạy kịch bản giả lập RAG pipeline đầy đủ:
```powershell
python -m tests.mock_pipeline_test
```
*(Chạy độc lập, tự động giả lập API Mistral và hiển thị đầy đủ các thông tin mã băm, danh sách Stack hội thoại và trích xuất file log thực tế).*

### 2️⃣ Chạy kiểm thử tích hợp toàn luồng qua API REST (Yêu cầu khởi chạy backend):
*   **Bật Server Backend (Terminal 1):**
    ```powershell
    python manage.py runserver 8001
    ```
*   **Chạy luồng test (Terminal 2):**
    ```powershell
    python -m tests.mock_frontend_backend_test --flow full
    ```
