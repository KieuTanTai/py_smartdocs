import sys
import os
import io
import time
import datetime
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

# Fix Windows console encoding for Unicode/Emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Setup Django configuration
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")
import django
django.setup()

# Import backend classes
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.enums.e_provider_name import EProviderName
from backend.apps.llm.llm_ocr.llm_ocr_factory import LLMOCRFactory
from backend.apps.llm.llm_ocr.mistral_uploader import MistralUploader
from backend.apps.services.rag_base.storage.storage_service import FileStorageService
from backend.apps.services.rag_base.extract.extract_content_service import ExtractContentService
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.services.chat.models import ConversationModel, MessageModel

# Define stack structure for sorting conversations by datetime (newest at the top)
class ConversationStack:
    def __init__(self):
        self.stack = []

    def push(self, conversation: ConversationModel):
        """Push a conversation onto the stack and keep it sorted newest first."""
        self.stack.append(conversation)
        self.stack.sort(key=lambda x: x.conversation_created_at, reverse=True)
        DEFAULT_LOGGER.info(
            f"Pushed conversation '{conversation.conversation_title}' onto the stack.",
            source=str(self.__class__)
        )

    def pop(self) -> ConversationModel:
        """Pop the newest conversation from the stack."""
        if not self.stack:
            return None
        popped = self.stack.pop(0)
        DEFAULT_LOGGER.info(
            f"Popped conversation '{popped.conversation_title}' from the stack.",
            source=str(self.__class__)
        )
        return popped

    def list_all(self) -> list[ConversationModel]:
        """List all conversations currently in the stack (sorted newest first)."""
        return self.stack


@patch("backend.apps.llm.llm_ocr.mistral_uploader.Mistral")
@patch("backend.apps.llm.llm_ocr.mistral_ocr.Mistral")
def run_mock_pipeline_test(MockMistralOCR, MockMistralUploader):
    print("================================================================================")
    print("🧪 Starting Mock Integration Test: Upload - Storage - OCR - Normalize - Hashing")
    print("================================================================================")

    # 1. Setup mock clients for Mistral services
    mock_uploader_client = MagicMock()
    mock_upload_resp = MagicMock()
    mock_upload_resp.id = "mock-mistral-file-id-xyz123"
    mock_upload_resp.size_bytes = 4096
    mock_upload_resp.mimetype = "text/plain"
    mock_uploader_client.files.upload.return_value = mock_upload_resp
    MockMistralUploader.return_value = mock_uploader_client

    mock_ocr_client = MagicMock()
    mock_ocr_resp = MagicMock()
    mock_page = MagicMock()
    mock_page.markdown = "## MOCK SCAN RESULTS\nBáo cáo tài chính năm 2025 Kiểm toán.\nDoanh thu đạt: 1,500 tỷ VND."
    mock_ocr_resp.pages = [mock_page]
    mock_ocr_client.ocr.process.return_value = mock_ocr_resp
    MockMistralOCR.return_value = mock_ocr_client

    # 2. Instantiate backend classes
    logger = DEFAULT_LOGGER
    factory = LLMOCRFactory(DEFAULT_CONFIG_PROVIDER, logger)
    uploader = MistralUploader(logger)

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    storage_dir = output_dir / "storage"

    storage = FileStorageService(storage_dir, uploader, logger)
    extract_content = ExtractContentService(factory, storage, logger)

    # Create dummy local file to upload
    dummy_file = output_dir / "dummy_invoice.txt"
    dummy_file.write_text("DUMMY INVOICE CONTENT FOR TESTING OCR PIPELINE", encoding="utf-8")

    # 3. Execute Pipeline: Upload & Storage
    print("\n[Step 1] Uploading and storing file...")
    file_info = storage.save_file(dummy_file)
    print(f"  → File uploaded to storage successfully. File ID: {file_info.id}")

    # 4. Execute Pipeline: Scan OCR
    print("\n[Step 2] Scanning OCR via Mistral...")
    # Recreate the file since the previous save_file step moved the original file to storage directory
    dummy_file.write_text("DUMMY INVOICE CONTENT FOR TESTING OCR PIPELINE", encoding="utf-8")
    ocr_response = extract_content.extract_from_file_text(dummy_file, EProviderName.MISTRAL)
    raw_content = ocr_response.content if hasattr(ocr_response, "content") else ocr_response
    print(f"  → OCR processing completed.")

    # 5. Execute Pipeline: Normalize Content
    print("\n[Step 3] Normalizing OCR content...")
    normalizer = Normalize(logger)
    normalized_content = normalizer.normalize(raw_content)
    print(f"  → Normalized text:\n    {normalized_content}")

    # 6. Execute Pipeline: Hashing
    print("\n[Step 4] Hashing normalized content...")
    doc_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
    print("  +--------------------------------------------------------------+")
    print(f"  | 🔥 GENERATED SHA-256 HASH: {doc_hash} |")
    print("  +--------------------------------------------------------------+")

    # 7. Mock Conversation Stack Behavior
    print("\n[Step 5] Creating Conversation and pushing to Stack...")
    stack = ConversationStack()

    # Pre-populate stack with simulated older conversations
    from django.utils import timezone
    for offset in [15, 10, 5]:
        dt = timezone.now() - datetime.timedelta(minutes=offset)
        title = f"Simulated Chat - {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        c = ConversationModel(conversation_title=title)
        c.conversation_created_at = dt
        stack.push(c)

    # Create actual conversation in Django DB with title + datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conv_title = f"RAG Doc Review - {now_str}"
    db_conv = ConversationModel.objects.create(conversation_title=conv_title)
    
    # Reload from DB to obtain auto_now_add creation time
    db_conv.refresh_from_db()
    stack.push(db_conv)

    print("\n[Step 6] Listing all Stack conversations (newest first):")
    for idx, c in enumerate(stack.list_all(), 1):
        print(f"   {idx}. {c.conversation_title} (Created: {c.conversation_created_at})")

    # 8. Print Hash into the Chat block
    print("\n[Step 7] Printing document hash code to conversation chat block...")
    bootstrap_text = f"Hello! I have indexed the document. Document Hash Code: {doc_hash}"
    message = MessageModel.objects.create(
        message_conversation=db_conv,
        message_is_user_send=False,
        message_content=bootstrap_text
    )
    print(f"  🤖 Assistant initial message: '{message.message_content}'")

    # 9. Verify log generation in docs folder
    print("\n[Step 8] Verifying log files generated in docs directory...")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log_dir = Path(__file__).resolve().parents[1] / "docs" / "logs" / today_str
    log_file = log_dir / f"{today_str}.log"
    if log_file.exists():
        print(f"  ✅ Log file successfully generated at: {log_file}")
        # Print tail of the log file
        log_lines = log_file.read_text(encoding="utf-8").splitlines()
        print("  Snippet of generated logs:")
        for line in log_lines[-12:]:
            print(f"    {line}")
    else:
        print(f"  ❌ Log file not found at: {log_file}")

    print("\n================================================================================")
    print("✅ Mock Integration Test Pipeline Executed Successfully!")
    print("================================================================================")


if __name__ == "__main__":
    run_mock_pipeline_test()
