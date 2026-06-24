"""
Test RAG context building to verify the bug fix
"""
import os
import sys
import django
from pathlib import Path
import json

# Setup Django
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.local')
django.setup()

from backend.apps.services.chat.models import DocumentModel, ConversationModel
from sys_services.system_dirs import METADATA_DIR

def check_metadata_files():
    """Check if metadata files exist and which IDs they use"""
    print("\n" + "="*60)
    print("Checking Metadata Files")
    print("="*60)
    
    metadata_docs_dir = METADATA_DIR / "docs"
    if not metadata_docs_dir.exists():
        print(f"❌ Metadata directory does not exist: {metadata_docs_dir}")
        return
    
    json_files = list(metadata_docs_dir.glob("*.json"))
    print(f"Found {len(json_files)} metadata files")
    
    # Check a sample file
    if json_files:
        sample_file = json_files[0]
        with open(sample_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        print(f"\nSample metadata file: {sample_file.name}")
        print(f"  document_id: {metadata.get('document_id', 'NOT FOUND')}")
        print(f"  file_name: {metadata.get('file_name', 'NOT FOUND')}")
        print(f"  chunk_count: {metadata.get('chunk_count', 0)}")


def check_document_records():
    """Check document records in database"""
    print("\n" + "="*60)
    print("Checking Document Records in Database")
    print("="*60)
    
    docs = DocumentModel.objects.all().order_by('-documents_created_at')[:5]
    
    print(f"Found {DocumentModel.objects.count()} total documents")
    print(f"Showing last 5:")
    
    for doc in docs:
        print(f"\n  Document ID: {doc.document_id}")
        print(f"  Conversation ID: {doc.documents_conversation.conversations_id if doc.documents_conversation else 'None'}")
        print(f"  File Path: {doc.documents_file_path or 'None'}")
        print(f"  Status: {doc.documents_status}")
        
        # Check if metadata file exists for this document
        document_id = str(doc.document_id)
        metadata_path = METADATA_DIR / "docs" / f"{document_id}.json"
        metadata_exists = metadata_path.exists()
        
        print(f"  Metadata file exists: {'✅' if metadata_exists else '❌'}")
        
        if doc.documents_conversation:
            # Check if FAISS index exists
            conv_id = str(doc.documents_conversation.conversations_id)
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            faiss_path = METADATA_DIR / "faiss" / today / f"{conv_id}.faiss"
            faiss_exists = faiss_path.exists()
            print(f"  FAISS index exists: {'✅' if faiss_exists else '❌'}")


def check_conversation_document_mapping():
    """Check the relationship between conversations and documents"""
    print("\n" + "="*60)
    print("Checking Conversation-Document Mapping")
    print("="*60)
    
    convs = ConversationModel.objects.all().order_by('-conversations_created_at')[:3]
    
    for conv in convs:
        print(f"\n  Conversation ID: {conv.conversations_id}")
        print(f"  Title: {conv.conversations_title or conv.conversations_name or 'Untitled'}")
        
        # Find documents for this conversation
        docs = DocumentModel.objects.filter(documents_conversation=conv)
        print(f"  Documents attached: {docs.count()}")
        
        for doc in docs:
            print(f"    - Document ID: {doc.documents_id}")
            print(f"      File: {Path(doc.documents_file_path).name if doc.documents_file_path else 'Unknown'}")
            print(f"      Status: {doc.documents_status}")


def main():
    print("\n" + "="*60)
    print("RAG Context Metadata Test")
    print("="*60)
    print("\nThis script checks if metadata files are stored by document_id")
    print("and verifies the fix for the RAG context retrieval bug.")
    
    check_metadata_files()
    check_document_records()
    check_conversation_document_mapping()
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)
    print("\nKey Findings:")
    print("- Metadata files should be indexed by document_id")
    print("- FAISS indices should be indexed by conversation_id")
    print("- The code should use the correct ID for each lookup")
    print("\n")


if __name__ == "__main__":
    main()
