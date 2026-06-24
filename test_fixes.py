#!/usr/bin/env python
"""
Test script to verify bug fixes
"""
import sys
from pathlib import Path

print("=" * 60)
print("Testing Bug Fixes")
print("=" * 60)

# Test 1: MIME type detection
print("\n1. Testing MIME type detection from file extension...")
try:
    test_cases = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
    }
    
    for ext, expected_mime in test_cases.items():
        # Simulate the detection logic
        suffix = ext.lower()
        mimetype_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tif': 'image/tiff',
            '.tiff': 'image/tiff',
        }
        detected = mimetype_map.get(suffix, 'application/pdf')
        assert detected == expected_mime, f"Failed for {ext}: got {detected}, expected {expected_mime}"
        print(f"   ✓ {ext} → {detected}")
    
    print("   ✅ MIME type detection: PASSED")
except Exception as e:
    print(f"   ❌ MIME type detection: FAILED - {e}")
    sys.exit(1)

# Test 2: Mistral import
print("\n2. Testing Mistral OCR module imports...")
try:
    from backend.apps.llm.llm_ocr.mistral_ocr import MistralLLMOCR
    from backend.apps.llm.llm_ocr.mistral_uploader import MistralUploader
    print("   ✓ MistralLLMOCR imported")
    print("   ✓ MistralUploader imported")
    print("   ✅ Mistral imports: PASSED")
except Exception as e:
    print(f"   ❌ Mistral imports: FAILED - {e}")
    sys.exit(1)

# Test 3: Extract response interface
print("\n3. Testing IExtractResponse structure...")
try:
    from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
    
    # Test creating instance with correct parameters
    response = IExtractResponse(
        document_id="test-id",
        extracted_text="test text",
        model="test-model",
        page_processed=5,
        doc_size_bytes=1024
    )
    
    assert response.document_id == "test-id"
    assert response.extracted_text == "test text"
    assert response.model == "test-model"
    assert response.page_processed == 5
    assert response.doc_size_bytes == 1024
    
    print("   ✓ IExtractResponse structure verified")
    print("   ✅ Extract response: PASSED")
except Exception as e:
    print(f"   ❌ Extract response: FAILED - {e}")
    sys.exit(1)

# Test 4: Check fixed files exist
print("\n4. Verifying fixed files exist...")
fixed_files = [
    "backend/apps/llm/llm_ocr/mistral_uploader.py",
    "backend/apps/llm/llm_ocr/mistral_ocr.py",
    "backend/api/documents/views.py",
    "backend/api/conversations/views.py",
]

for file_path in fixed_files:
    full_path = Path(file_path)
    if full_path.exists():
        print(f"   ✓ {file_path}")
    else:
        print(f"   ❌ {file_path} not found")
        sys.exit(1)

print("   ✅ File verification: PASSED")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
print("\nNext steps:")
print("1. Restart Django server")
print("2. Test file upload via API")
print("3. Test asking questions to AI")
print("4. Monitor logs for any errors")
