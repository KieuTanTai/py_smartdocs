TRƯỜNG ĐẠI HỌC SÀI GÒN
KHOA CÔNG NGHỆ THÔNG TIN
BÁO CÁO ĐỒ ÁN MÔN HỌC
PHÁT TRIỂN PHẦN MỀM MÃ NGUỒN MỞ
Đề tài: SmartDoc AI - Hệ thống hỏi đáp tài liệu thông minh (RAG System)
Sinh viên thực hiện:Mã Gia Uy - 3122410460
Kiều Tấn Tài - 3123410314
Nguyễn Tuấn Kiệt - 3123560044
Huỳnh Ánh Nghi - 3122410256
Giảng viên hướng dẫn:ThS. Từ Lãng Phiêu
Học kỳ:Spring 2026
TP. HỒ CHÍ MINH, NĂM 2026
MỤC LỤC
I Giới thiệu và công trình liên quan1
II Thực nghiệm1
II-A Luồng xử lý . . . . . . . . . 1
II-B Module Frontend . . . . . . 2
II-C Module Backend . . . . . . . 2
II-C1 Module Core . . . 2
II-C2 Module Documents 2
II-C3 Module Retrieval 2
II-C4 Module LLM . . 3
II-C5 Module Chat . . . 3
II-C6 Module Jobs . . . 3
II-D So sánh tính năng . . . . . . 3
III PHƯƠNG PHÁP KIỂM THỬ VÀ
ĐÁNH GIÁ HIỆU SUẤT4
III-A Bước 1: Thiết lập kịch bản
kiểm thử (Test Cases) . . . . 4
III-B Bước 2: Quy trình ghi nhận
số liệu . . . . . . . . . . . . 4
III-C Bước 3: Đánh giá độ chính
xác (Accuracy) . . . . . . . . 4
IV KẾT QUẢ THỰC NGHIỆM VÀ SO
SÁNH MÔ HÌNH4
V Kết luận4
VI Hướng phát triển5
VI-A Các vấn đề tồn tại và hướng
cải thiện . . . . . . . . . . . 5
VII Tài liệu tham khảo5
Tài liệu5
DANH SÁCH HÌNH VẼ
1 Biểu đồ hiệu năng phản hồi của 03 mô
hình thực nghiệm . . . . . . . . . . . 4
DANH SÁCH BẢNG
I So sánh SmartDoc AI với các giải pháp
khác . . . . . . . . . . . . . . . . . . 4
II Kết quả kiểm thử hiệu suất trên tệp
SmartDocsReq.pdf . . . . . . . . . . . 4
1
Bài tập lớn: Môn Phát triển phần mềm mã nguồn mở – Đại học Sài Gòn, 5-6/04/2026
SmartDoc AI- Intelligent Document QA System
Mã Gia Uy ∗, Nguyễn Tuấn Kiệt †, Kiều Tấn Tài ‡, Huỳnh Ánh Nghi
∗Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn, †Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn,
‡Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn
Email: magiauy46@gmail.com, nghihuynh1210@gmail.com, tuankiet10072005@gmail.com,kieutantai2x@gmail.com
Tóm tắt nội dung—Dự án này xây dựng một hệ
thống RAG (Retrieval-Augmented Generation) hoàn
chỉnh, cho phép người dùng tương tác với tài liệu PDF
thông qua ngôn ngữ tự nhiên. Hệ thống sử dụng mô
hình Qwen2:1.5b chạy cục bộ qua Ollama, kết hợp
với vector database FAISS và embedding đa ngôn ngữ
để đảm bảo độ chính xác và tính bảo mật dữ liệu
Keywords-RAG, LLM, Qwen2, FAISS, LangChain,
Xử lý ngôn ngữ tự nhiên.
I. GIỚI THIỆU VÀ CÔNG TRÌNH LIÊN QUAN
Trong kỷ nguyên số hiện nay, việc xử lý và tìm
kiếm thông tin từ các tài liệu điện tử đã trở thành một
nhu cầu thiết yếu. Với sự phát triển mạnh mẽ của
Trí tuệ nhân tạo (AI) và Xử lý ngôn ngữ tự nhiên
(NLP), các hệ thống RAG (Retrieval-Augmented
Generation) đã nổi lên như một giải pháp hiệu quả
cho bài toán này. Dự án này được thực hiện nhằm
xây dựng một hệ thống RAG hoàn chỉnh, cho phép
người dùng tải lên tài liệu PDF và đặt câu hỏi
về nội dung tài liệu. Hệ thống sử dụng mô hình
Qwen2:1.5b thông qua Ollama, kết hợp với công
nghệ embedding đa ngôn ngữ và vector database để
cung cấp câu trả lời chính xác cho cả tiếng Việt và
tiếng Anh. Báo cáo này trình bày chi tiết về kiến
trúc hệ thống, các công nghệ được sử dụng, quy
trình triển khai và kết quả đạt được
II. THỰC NGHIỆM
SmartDocsAI được xây dựng theo kiến trúc
microservices với nhiều thành phần độc lập giao
tiếp qua API và message queue. Hệ thống tách biệt
rõ ràng giữa các tầng: giao diện người dùng, logic
nghiệp vụ, xử lý bất đồng bộ, và lưu trữ dữ liệu.
• Lớp trình diễn:Sử dụng Streamlit để tạo giao
diện web
• Lớp ứng dụng:Sử dụng LangChain để quản
lý pipeline RAG và Prompt Engineering
• Lớp dữ liệu:Lưu trữ vector với FAISS và sử
dụng embedding MPNet 768 chiều, sử dụng
SQLite/MySQL với công nghệ Django ORM
để lưu trữ.
• Lớp nghiệp vụ:Django apps, Python 3.13 để
xử lý nghiệp vụ, PaddleOCR, External API
trích xuất văn bản PDF, Gemini API/ Sentence
Transformer dùng để vector hóa văn bản.
• Lớp mô hình:Chạy Qwen2:1.5b thông qua
Ollama local; Gemini API sinh câu trả lời.
Hệ thống gồm có 2 luồng dữ liệu chính:
A. Luồng xử lý
Luồng 1: Xử lý Tài liệu (Document
Processing Pipeline),→
Người dùng→Upload PDF→
DocumentUploadView,→
→UploadService.create_documents_ ⌋
from_files(),→
→Document.objects.create() [DB:
status=UPLOADED],→
→process_document.delay(id)
[Celery Task],→
↓(bất đồng bộ, worker riêng)
→run_document_pipeline(document)
→NormalizationService.normalize_ ⌋
document(),→
pypdf: extract_pdf_text()
[nếu PDF có text],→
OCRService.extract_text_fro ⌋
m_pdf() [nếu cần OCR],→
→ChunkingService.chunk() [Recurs ⌋
iveCharacterTextSplitter],→
→QdrantStore.upsert_document()
EmbeddingService.embed_text ⌋
s() [Gemini/BGE-M3],→
→Document.status = INDEXED [DB
update],→
Luồng 2: Hỏi-Đáp (RAG Query Pipeline)
Người dùng→Gõ câu hỏi→
ConversationMessageView.post(),→
→MessageService.send_message(con ⌋
versation_id, payload),→
→SearchService.search(query,
document_ids, limit=5),→
QdrantStore.search()
Bài tập lớn: Môn Phát triển phần mềm mã nguồn mở – Đại học Sài Gòn, 5-6/04/2026
EmbeddingService.embed ⌋
_query() [Gemini
RETRIEVAL_QUERY]
,→
,→
client.search() [Cosine
similarity, filter
by document_id]
,→
,→
→CompletionService.generate(prov ⌋
ider, model, prompt,
context_hits)
,→
,→
_build_prompt(): [SYSTEM] +
[CONTEXT] + [HISTORY] +
[QUESTION]
,→
,→
GeminiClient/OllamaClient.g ⌋
enerate(),→
→Message.objects.create(role=ASS ⌋
ISTANT, content=response),→
→SessionMemoryStore.append_turn()
[RAM cache],→
→Return {user_message,
assistant_message, hits},→
B. Module Frontend
Luồng tương tác người dùng:
1) Người dùng upload PDF qua
file_uploaderwidget.
2) Click Process, gửi POST /api/documents/
upload/.
3) Backend trả về document với process-
ing_status=’uploaded’.
4) Frontend lưu active_document_id, gọi
rerun().
5) Auto-polling: mỗi
POLL_INTERVAL_SECONDS (2s), gọi
GET /api/documents/{id}/status/.
6) Khi processing_status=’indexed’:
document_ready=True.
7) Người dùng nhập câu hỏi, submit form.
8)ensure_conversation() : tạo conversa-
tion nếu chưa có, poll đếnREADY.
9) Gửi POST /api/conversations/{id}/messages/
với câu hỏi.
10) Frontend nhận response, thực hiện re-
fresh_chat_history()vàrerun().
C. Module Backend
Backend được tổ chức theo dạng module, mỗi
module phụ trách một phần rõ ràng trong pipeline
RAG: từ xử lý tài liệu, indexing vector, xây dựng
prompt, điều phối chat, đến chạy jobs bất đồng bộ.
1) Module Core ( apps/core/):Module core
cung cấp các tiện ích dùng chung và chuẩn hoá
giao tiếp giữa backend và frontend.
• Envelope response: mọi API trả
về định dạng thống nhất suc-
cess/message/data.
•Exception handling thống nhất:
–ValidationError→ HTTP 400 (chi
tiết lỗi theo từng field).
–NotFound→ HTTP 404 (message thống
nhất).
– Server error → HTTP 500 (message an
toàn, không lộ stacktrace).
2) Module Documents ( apps/documents/):
Module Documents quản lý vòng đời tài liệu từ khi
upload đến khi indexed, sẵn sàng cho chat.
•Upload tài liệu→tạoDocumentrecord.
• Kích hoạt pipeline xử lý/indexing (thông qua
Celery jobs).
• Cập nhật trạng thái theo tiến trình: up-
loaded/processing/indexed/failed.
3) Module Retrieval ( apps/retrieval/):
Module Retrieval thực hiện toàn bộ pipeline RAG
cho indexing và retrieval.
NormalizationService (Extract + Normalize):
•Trích xuất (ưu tiên):
1) Kiểm tra file tồn tại trên disk.
2) Nếu PDF: trích xuất bằng PyPDF.
3) Nếu PDF scan (text rỗng): gọi OCR API.
4) Nếu không phải PDF: đọc text UTF-8 trực
tiếp.
5) Fallback: dùng document.title nếu
thất bại toàn bộ.
•Chuẩn hoá text:
–Collapse spaces/tabs liên tiếp→1 space.
– Collapse 3+ newlines liên tiếp → 2
newlines.
–Strip whitespace đầu/cuối mỗi đoạn.
– Tạo SHA-256 content hash để phát hiện
thay đổi nội dung.
ChunkingService (Chia nhỏ văn bản):
• Dùng RecursiveCharacter-
TextSplitter.
• Thứ tự ưu tiên khi split: \n\n→\n→.
→,→space→ký tự đơn.
• Cấu hình: chunk_size=700,
chunk_overlap=120.
• Overlap giúp hạn chế mất ngữ nghĩa giữa
các chunk liền kề.
EmbeddingService (Vector hoá):
• Vector hoá chunks (indexing time) và query
(query time) bằng Gemini Embedding.
Bài tập lớn: Môn Phát triển phần mềm mã nguồn mở – Đại học Sài Gòn, 5-6/04/2026
•Batch embedding với fallback:
–Thử batch embed với cấu hình dimension.
– Nếu fail → thử batch embed không
dimension.
–Nếu vẫn fail→fallback embed từng text.
•Task types:
–RETRIEVAL_DOCUMENT : embed chunks
từ tài liệu (indexing).
–RETRIEVAL_QUERY : embed câu hỏi
người dùng (query).
• Fallback khi API lỗi: khi EMBED-
DING_STRICT=False, sinh vector
deterministic từ SHA-256 để tránh gián đoạn
pipeline (đổi lại chất lượng search giảm).
OCRService (PDF scan):
•AI Studio Job Mode (Async Polling):
1) Submit job (POST file)→nhậnjobId.
2) Polling GET /jobs/{jobId} mỗi
poll_seconds.
3) Kiểm tra state: run-
ning/failed/done.
4) Nếudone: download result từjsonUrl.
5) Parse markdown từ layoutParsingRe-
sults.
• Timeout mặc định: 300s (cấu hình qua
PADDLEOCR_JOB_TIMEOUT_SECONDS).
QdrantStore (Vector DB adapter):
• Upsert (indexing): ensure collection →
embed chunks → upsert points (payload gồm
document_id,chunk_index,text).
• Search (query time): embed query →
filter theo document_id (chỉ search trong
documents đang chat)→trả về top-K hits.
4) Module LLM ( apps/llm/):Module LLM
triển khai Provider Pattern để dễ thêm/thay LLM
provider.
• ProviderFactory chọn client theo provider
name:gemini/ollama/mock.
• CompletionService build prompt RAG theo
cấu trúc: [SYSTEM]→[CONTEXT]→
[CHAT_HISTORY]→[QUESTION]→
[INSTRUCTION].
•Ràng buộc system prompt:
–Chỉ trả lời dựa trênCONTEXT.
– Nếu thiếu thông tin: Tài liệu không
đề cập đến.
–Không tự suy diễn ngoài tài liệu.
5) Module Chat ( apps/chat/):Module Chat
quản lý Conversation/Message và điều phối pipeline
RAG khi chat.
ConversationService:
• Nếu tất cả documents đã indexed →
status=READY.
• Nếu còn document chưa indexed →
status=PREPARING.
• Enqueue task chuẩn bị conversation sau khi
tạo.
MessageService (Trung tâm điều phối RAG):
1) Kiểm tra conversation READY (chưa sẵn sàng
→409).
2) Lấy chat history từ memory hoặc DB.
3) Lưu user message.
4) Search top-K context chunks.
5) Generate completion từ prompt đầy đủ.
6) Lưu assistant message (kèm latency/tokens).
7) Cập nhật memory store.
8) Trả về messages và hits.
SessionMemoryStore (In-memory history):
• Dùng FIFO (deque maxlen) để giới hạn lịch
sử.
•Đồng bộ DB–Memory:
–Memory rỗng→load từ DB.
–Restart lệch state→sync lại từ DB.
–Mỗi turn→append để dùng cho lần sau.
6) Module Jobs ( apps/jobs/):Module Jobs
chứa Celery tasks xử lý bất đồng bộ.
process_documenttask:
1) SetDocument.status=PROCESSING.
2) Chạy pipeline chính.
3) Cập nhật DocumentIndex (chunk_count,
vector_collection).
4) Set Document.status=INDEXED,
summary_status=READY.
5) Nếu lỗi →FAILED và lưu er-
ror_message.
Pipeline chính orchestrate:
• Normalize → Chunk → Upsert/Index →
Summarize.
prepare_conversationtask:
•Kiểm tra/đợi tất cả document đã indexed.
• Khi đủ điều kiện → đánh dấu conversation
READY.
D. So sánh tính năng
Hệ thống được đối chiếu với các giải pháp phổ
biến để đánh giá ưu thế về quyền riêng tư và chi
phí.
Bài tập lớn: Môn Phát triển phần mềm mã nguồn mở – Đại học Sài Gòn, 5-6/04/2026
Bảng I
SO SÁNHSMARTDOCAIVỚI CÁC GIẢI PHÁP KHÁC
Tính năng SmartDoc AI ChatGPT Local LLM
Riêng tư Có Không Có
Chi phí Miễn phí Trả phí Miễn phí
Tải tài liệu Có Có Không
Tốc độ Nhanh Rất nhanh Chậm
III. PHƯƠNG PHÁP KIỂM THỬ VÀ ĐÁNH GIÁ
HIỆU SUẤT
Để đảm bảo tính khách quan, quá trình đánh giá
được thực hiện thông qua việc so sánh trực tiếp
năng lực của 03 mô hình trên cùng một môi trường
và dữ liệu đầu vào.
A. Bước 1: Thiết lập kịch bản kiểm thử (Test Cases)
Nhóm thực hiện sử dụng phương pháp kiểm soát
biến số để đo lường chính xác sự chênh lệch hiệu
năng:
• Tài liệu thử nghiệm:Sử dụng duy nhất 01
tệp tin đại diện ( SmartDocsReq.pdf) làm
ngữ cảnh cho cả 03 mô hình.Việc này đảm bảo
khâu truy xuất (Retrieval) trả về kết quả tương
đương, từ đó làm nổi bật sự khác biệt ở khâu
xử lý của LLM.
• Kịch bản câu hỏi (Queries):Mỗi mô hình
được thử nghiệm với 02 dạng câu hỏi cốt lõi:
– Câu hỏi trích xuất sự thật (Fact-based):
Kiểm tra khả năng tìm kiếm con số cụ thể
trong tài liệu.
– Câu hỏi tóm tắt (Summarization):Kiểm tra
khả năng tổng hợp nội dung chính của toàn
bộ tài liệu.
B. Bước 2: Quy trình ghi nhận số liệu
Số liệu được ghi nhận thông qua tính năngLatency
Breakdowntích hợp sẵn trong hệ thống:
1) Đo lường xử lý (Processing):Ghi lại thời gian
Query(truy xuất vector từ Qdrant) và đặc biệt
là thời gianGeneration(thời gian mô hình sinh
câu trả lời).
2) Tính toán trung bình:Thực hiện các lượt
truy vấn và tính giá trị trung bình cộng cho
thông sốGenerationnhằm đưa ra con số thực
nghiệm cuối cùng cho báo cáo.
C. Bước 3: Đánh giá độ chính xác (Accuracy)
Chất lượng câu trả lời được nhóm thực hiện đánh
giá thủ công dựa trên nội dung gốc của tài liệu theo
thang điểm 1-10. Điểm số này phản ánh khả năng
đọc hiểu và mức độ trung thực của mô hình đối với
ngữ cảnh được cung cấp.
IV. KẾT QUẢ THỰC NGHIỆM VÀ SO SÁNH MÔ
HÌNH
Dưới đây là bảng tổng hợp kết quả thực nghiệm
sau khi áp dụng quy trình kiểm thử trên 01 tệp tài
liệu duy nhất cho 03 mô hình:
Bảng II
KẾT QUẢ KIỂM THỬ HIỆU SUẤT TRÊN TỆP
SMARTDOCSREQ.PDF
Mô hình Thời gian Generation (s) Độ chính xác
Qwen2:1.5b (Local) 22.29 3.0 / 10
Gemini 2.5 Flash (API) 2.48 10.0 / 10
Gemini 2.5 Pro (API) 6.36 10.0 / 10
Gemini Flash Gemini Pro Qwen2 (Local)
0
5
10
15
20
25
2.48
6.36
22.29
Thời gian Generation trung bình (giây)
So sánh tốc độ sinh văn bản trên cùng một ngữ cảnh
Hình 1. Biểu đồ hiệu năng phản hồi của 03 mô hình thực nghiệm
Nhận xét kết quả:Việc thử nghiệm trên cùng
một tệp tin cho thấy sự chênh lệch rõ rệt về năng
lực xử lý. Trong khi khâu truy xuất (Query) luôn
ổn định ở mức dưới 20ms, mô hìnhQwen2:1.5b
(Local)tốn trung bình hơn 22 giây và có tỉ lệ trả
lời sai cao.Ngược lại, các mô hình API nhưGemini
2.5 Flashcho thấy sự ưu việt về cả tốc độ ( ∼2.5
giây) lẫn độ chính xác tuyệt đối trong việc trích
xuất và tóm tắt thông tin.
V. KẾT LUẬN
Hệ thống SmartDocsAI là một dự án RAG được
thiết kế và implement ở mức độ tốt, phù hợp cho
Bài tập lớn: Môn Phát triển phần mềm mã nguồn mở – Đại học Sài Gòn, 5-6/04/2026
môi trường học tập và prototype. Mã nguồn thể hiện
hiểu biết vững chắc về các khái niệm RAG, kiến
trúc Django, và thiết kế hệ thống.
VI. HƯỚNG PHÁT TRIỂN
Trong tương lai, dự án sẽ mở rộng hỗ trợ file
DOCX, tích hợp bộ nhớ hội thoại để xử lý các câu
hỏi tiếp nối và cải thiện chiến lược chia nhỏ văn
bản. Ngoài ra, các hạn chế hiện tại sẽ được ưu tiên
khắc phục với các hướng cải thiện sau:
A. Các vấn đề tồn tại và hướng cải thiện
1. Bảo mật Authentication:
Hiện nay hệ thống không có authentica-
tion/authorization, toàn bộ API đều public. Đây
là điểm yếu lớn cho môi trường production.
• Cần bổ sung user management và phân quyền
truy cập.
• Thêm JWT/session-based authentication cho
các endpoint.
•Cần có rate limiting để tránh abuse API.
• Thực hiện input sanitization (nhất là tên file)
để tăng an toàn bảo mật.
2. Session Memory Không Persist:
SessionMemoryStore hiện lưu trong RAM, nên
mất hết khi restart, không chia sẻ giữa nhiều
server instance.
• Chuyển sang sử dụng Redis (hoặc caching
layer có distributed support) để lưu session với
TTL phù hợp.
• Đảm bảo trải nghiệm liên tục (kể cả khi server
scale hoặc deploy lại).
3. Thiếu File Type Validation:
UploadService chỉ dựa vào mime_type từ request,
không kiểm tra magic bytes. Người dùng có thể
upload file không phải PDF.
• Cần kiểm tra magic bytes/headers thực tế của
file để xác định kiểu file chuẩn xác.
• Từ chối hoặc cảnh báo nếu file không hợp lệ
với định dạng chấp nhận.
4. Orphaned Qdrant Points:
Không có cơ chế cleanup các vector points khi
xoá Document, dẫn đến dữ liệu cũ tồn tại không
kiểm soát trong Qdrant.
• Bổ sung logic xoá các Qdrant points liên quan
khi tài liệu bị xoá khỏi hệ thống.
• Có thể viết batch job định kỳ xoá dữ liệu mồ
côi.
5. Thiếu Pagination:
DocumentListView và ConversationListCreate-
View chưa có pagination, gây chậm và tốn
memory với nhiều tài liệu.
• Bổ sung cơ chế phân trang (pagination) cho
các API trả danh sách lớn.
•Tối ưu query, giới hạn page size mặc định.
6. Giới hạn Single File Upload ở Frontend:
Frontend hiện chỉ xử lý document đầu tiên trong
mảng trả về, không hỗ trợ multi-file selection
trong một phiên chat.
• Nâng cấp giao diện để cho phép upload và xử
lý nhiều file cùng lúc.
• Đảm bảo backend và retrieval pipeline hỗ trợ
xử lý parallel multi-file.
VII. TÀI LIỆU THAM KHẢO
TÀI LIỆU
[1] Django Documentation:
https://docs.djangoproject.com/en/5.2/
[2] Django REST Framework:
https://www.django-rest-framework.org/
[3] Celery Documentation:
https://docs.celeryq.dev/en/stable/
[4] Qdrant Documentation:
https://qdrant.tech/documentation/
[5] Gemini API: https://ai.google.dev/gemini-api
[6] LangChain Text Splitters: https://python.langchain.
com/docs/concepts/text_splitters/
[7] BAAI/bge-m3: https://huggingface.co/BAAI/bge-m3
[8] PaddleOCR:
https://paddlepaddle.github.io/PaddleOCR/
[9] Ollama: https://ollama.ai/
[10] Streamlit Documentation: https://docs.streamlit.io/
