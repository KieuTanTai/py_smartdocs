import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.local')
django.setup()

from backend.apps.services.chat.models import DocumentModel, ConversationModel, ConversationFilesModel, MessageModel

print("--- Testing ConversationModel CRUD, Filters, and Ordering ---")
try:
    # 1. Create using conversations_title (prefixed keyword)
    conv1 = ConversationModel.objects.create(conversations_title="Test Conversation 1")
    print(f"SUCCESS: Created conversation 1. Title: '{conv1.conversation_title}', ID: {conv1.conversation_id}")

    # 2. Create using conversation_title (singular keyword)
    conv2 = ConversationModel.objects.create(conversation_title="Test Conversation 2")
    print(f"SUCCESS: Created conversation 2. Title: '{conv2.conversation_title}', ID: {conv2.conversation_id}")

    # 3. Filter using singular field name
    matches = ConversationModel.objects.filter(conversation_title="Test Conversation 1")
    print(f"SUCCESS: Filtered by conversation_title. Count: {matches.count()}")

    # 4. Filter using plural/prefixed field name (this won't work in Django ORM filter since it's a property)
    # We shouldn't use it in filter, but let's check ordering by singular field
    convs_ordered = ConversationModel.objects.all().order_by("-conversation_created_at")
    print(f"SUCCESS: Ordered conversations by conversation_created_at. Count: {convs_ordered.count()}")

    # 5. Retrieve properties
    print(f"Property conversions_title: '{conv1.conversations_title}'")
    print(f"Property conversations_created_at: {conv1.conversations_created_at}")

    conv1.delete()
    conv2.delete()
except Exception as e:
    import traceback
    print("FAILED: ConversationModel tests failed.")
    traceback.print_exc()

print("\n--- Testing DocumentModel CRUD and Filters ---")
try:
    conv = ConversationModel.objects.create(conversation_title="Doc Test Conv")
    
    # 1. Create with documents_ status/path (prefixed)
    doc1 = DocumentModel.objects.create(
        documents_conversation=conv,
        documents_file_path="doc1.pdf",
        documents_status="uploaded",
        documents_content="Doc 1 content"
    )
    print(f"SUCCESS: Created Document 1. ID: {doc1.document_id}")

    # 2. Filter by singular 'status'
    indexed_docs = DocumentModel.objects.filter(status="uploaded")
    print(f"SUCCESS: Filtered by status='uploaded'. Count: {indexed_docs.count()}")

    # 3. Access property attributes
    print(f"Property status: '{doc1.status}'")
    print(f"Property content: '{doc1.content}'")
    print(f"Property faiss_index_file_name: '{doc1.faiss_index_file_name}'")

    doc1.delete()
    conv.delete()
except Exception as e:
    import traceback
    print("FAILED: DocumentModel tests failed.")
    traceback.print_exc()

print("\n--- Testing ConversationFilesModel Relations and Filters ---")
try:
    conv = ConversationModel.objects.create(conversation_title="File Test Conv")
    doc = DocumentModel.objects.create(
        conversation=conv,
        file_path="test_file.docx",
        status="indexed",
        content="Hello RAG"
    )

    # 1. Create relationship using singular conversation and faiss_index
    cf = ConversationFilesModel.objects.create(
        conversation=conv,
        faiss_index=doc
    )
    print(f"SUCCESS: Created ConversationFiles relationship. ID: {cf.conversation_files_id}")

    # 2. Filter using conversation
    cf_filter = ConversationFilesModel.objects.filter(conversation=conv)
    print(f"SUCCESS: Filtered ConversationFiles by conversation. Count: {cf_filter.count()}")

    # 3. Filter using faiss_index_id
    cf_filter_index = ConversationFilesModel.objects.filter(faiss_index_id=doc.document_id)
    print(f"SUCCESS: Filtered ConversationFiles by faiss_index_id. Count: {cf_filter_index.count()}")

    cf.delete()
    doc.delete()
    conv.delete()
except Exception as e:
    import traceback
    print("FAILED: ConversationFilesModel tests failed.")
    traceback.print_exc()

print("\n--- Columns in DB tables inspection ---")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(documents);")
        print("Columns in 'documents' table:")
        for r in cursor.fetchall():
            print(f"  - {r[1]} ({r[2]})")
            
        cursor.execute("PRAGMA table_info(conversations);")
        print("Columns in 'conversations' table:")
        for r in cursor.fetchall():
            print(f"  - {r[1]} ({r[2]})")
            
        cursor.execute("PRAGMA table_info(conversation_files);")
        print("Columns in 'conversation_files' table:")
        for r in cursor.fetchall():
            print(f"  - {r[1]} ({r[2]})")
except Exception as e:
    import traceback
    print("FAILED: Could not inspect DB structure.")
    traceback.print_exc()
