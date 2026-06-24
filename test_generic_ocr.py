"""
Quick test script to verify the GenericOCR implementation works correctly.
Run this before starting the server to ensure everything is set up properly.
"""
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_generic_ocr_import():
    """Test that we can import the GenericOCR class."""
    try:
        from backend.apps.llm.llm_ocr.generic_ocr import GenericOCR
        print("✅ GenericOCR import successful")
        return True
    except ImportError as e:
        print(f"❌ Failed to import GenericOCR: {e}")
        return False

def test_factory_import():
    """Test that we can import the updated factory."""
    try:
        from backend.apps.llm.llm_ocr.llm_ocr_factory import LLMOCRFactory
        print("✅ LLMOCRFactory import successful")
        return True
    except ImportError as e:
        print(f"❌ Failed to import LLMOCRFactory: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    success = True
    
    try:
        import pypdf
        print("✅ pypdf is available")
    except ImportError:
        print("❌ pypdf is not installed")
        success = False
    
    try:
        import docx
        print("✅ python-docx is available")
    except ImportError:
        print("❌ python-docx is not installed")
        success = False
    
    return success

def test_enum_values():
    """Test that provider enum values are correct."""
    try:
        from backend.apps.core.enums.e_provider_name import EProviderName
        
        providers = [EProviderName.GEMINI, EProviderName.OLLAMA, EProviderName.MISTRAL]
        print(f"✅ Provider enums available: {[p.value for p in providers]}")
        return True
    except Exception as e:
        print(f"❌ Failed to load provider enums: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing GenericOCR Implementation")
    print("=" * 60)
    print()
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Enum Values", test_enum_values),
        ("GenericOCR Import", test_generic_ocr_import),
        ("Factory Import", test_factory_import),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        print("-" * 40)
        results.append(test_func())
    
    print()
    print("=" * 60)
    if all(results):
        print("✅ All tests passed! You can now start the server.")
    else:
        print("❌ Some tests failed. Please fix the issues before starting the server.")
    print("=" * 60)
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
