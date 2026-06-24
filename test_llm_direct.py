"""
Test LLM providers directly through the application layer
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.local')
django.setup()

from backend.apps.config import container
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.llm.llm_provider_factory import LLMProviderFactory

# Initialize container
__container = container.BackendContainer()

def test_provider(provider_name: str, model_name: str):
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} with model {model_name}")
    print(f"{'='*60}")
    
    try:
        # Create factory and get provider
        factory = LLMProviderFactory(__container.config_provider(), __container.log_pool())
        provider_enum = EProviderName(provider_name)
        llm_client = factory.get_provider(provider_enum, file_caller="test_llm_direct")
        
        print(f"✓ Created LLM client for {provider_name}")
        
        # Create completion request
        completion_req = ICompletionRequest(
            provider=provider_enum,
            model=model_name,
            prompt="Say 'Hello from Django!' in one sentence.",
        )
        
        print(f"✓ Created completion request")
        print(f"  Provider: {completion_req.provider}")
        print(f"  Model: {completion_req.model}")
        print(f"  Prompt: {completion_req.prompt}")
        
        # Generate response
        print(f"\nCalling generate()...")
        completion_resp = llm_client.generate(completion_req, file_caller="test_llm_direct")
        
        print(f"✓ Generated response")
        print(f"  Content: {completion_resp.content}")
        print(f"  Model: {completion_resp.model_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("Django LLM Integration Test")
    print("="*60)
    
    results = {}
    
    # Test Gemini
    results["Gemini"] = test_provider("gemini", "gemini-3.1-flash-lite")
    
    # Test Mistral  
    results["Mistral"] = test_provider("mistral", "mistral-large-latest")
    
    # Test Ollama
    results["Ollama"] = test_provider("ollama", "qwen2.5:1.5b-instruct")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for provider, status in results.items():
        status_str = "✅ WORKING" if status else "❌ FAILED"
        print(f"{provider}: {status_str}")


if __name__ == "__main__":
    main()
