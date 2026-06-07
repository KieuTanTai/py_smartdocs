import os
import sys
import django
import numpy as np

# =====================================================================
# BƯỚC 1: THIẾT LẬP MÔI TRƯỜNG DJANGO NỀN TẢNG
# =====================================================================
sys.path.append(r"D:\Git\Repo\py_smartdocs")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.apps.config.settings") 
try:
    django.setup()
    print("[OK] Đã nạp thành công môi trường cấu hình Django.")
except Exception as e:
    print(f"[ERROR] Thất bại khi nạp môi trường Django: {e}")
    sys.exit(1)

# =====================================================================
# BƯỚC 2: IMPORT THEO ĐÚNG PHÂN TẦNG KIẾN TRÚC CỦA BẠN
# =====================================================================
from backend.apps.application.conversations.conversation import UploadApplication
from backend.apps.config.container import container

# Giả lập định dạng file của request.FILES từ Django API gửi xuống
class MockDjangoUploadedFile:
    def __init__(self, file_path):
        self.name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            self._content = f.read()
            
    def read(self):
        return self._content

# =====================================================================
# BƯỚC 3: KỊCH BẢN CHẠY THỬ NGHIỆM ĐỒNG BỘ
# =====================================================================
def run_integration_test():
    # Đường dẫn file thực tế trên máy của bạn để chạy test băm nhỏ văn bản
    target_file = r"C:\Users\minhn\Downloads\phanlop.docx"
    
    if not os.path.exists(target_file):
        print(f"\n[LỖI]: Không tìm thấy file test tại đường dẫn: {target_file}")
        print("-> Vui lòng kiểm tra lại vị trí hoặc thay bằng một file .docx/.pdf có sẵn trên máy của bạn.")
        return

    print(f"\n--- BẮT ĐẦU TEST LUỒNG UPLOAD FILE: {os.path.basename(target_file)} ---")
    
    # Giả lập bọc file thô thành định dạng hệ thống nhận diện
    mock_files = [MockDjangoUploadedFile(target_file)]
    
    # GỌI TẦNG 1: APPLICATION LAYER
    print("\n[TẦNG APPLICATION]: Tiếp nhận dữ liệu, xử lý nghiệp vụ...")
    app_service = UploadApplication()
    
    # Hàm này sẽ tự động sinh file_id (UUID), đóng gói, và đẩy sang Job Manager Factory
    response = app_service.handle_uploaded_files(mock_files)
    
    print("\n[KẾT QUẢ PHẢN HỒI NHANH CHO CLIENT]:")
    print(response)
    
    file_id = response.get('file_ids')[0] if response.get('file_ids') else None
    
    if not file_id:
        print("\n[LỖI]: Tầng Application không sinh được file_id hợp lệ.")
        return

    # KIỂM TRA TẦNG HẬU TRƯỜNG: SERVICES (REDIS CACHE)
    print("\n[TẦNG SERVICES]: Truy vấn kiểm tra dữ liệu ngầm trong Redis Cache...")
    
    # Lấy đối tượng Service thực tế ra từ bộ quản lý IoC Container trung tâm
    storage_service = container.get_storage_service()
    cache_service = storage_service.cache_service
    
    # Kiểm tra xem key "file_id" đã được lưu trữ danh sách các cặp Chunks gối đầu chưa
    cached_chunks = cache_service.get(file_id)
    
    if cached_chunks:
        print(f"\n[THÀNH CÔNG]: Đã tìm thấy dữ liệu cấu trúc chunk của file_id '{file_id}' trong Redis!")
        print(f"-> Số lượng chunk tìm thấy: {len(cached_chunks)}")
        print("-> Cấu trúc phần tử đầu tiên (file_id:chunk_index):")
        print(f"Key ID: {cached_chunks[0][0]}")
        print(f"Nội dung text: {cached_chunks[0][1][:100]}...") # In thử 100 ký tự đầu tiên
    else:
        print(f"\n[CẢNH BÁO]: Không tìm thấy dữ liệu trong Redis.")
        print("-> Nguyên nhân: Có thể do Redis Server chưa được bật, hoặc các Task xử lý trích xuất/băm chữ gặp lỗi.")

if __name__ == "__main__":
    run_integration_test()