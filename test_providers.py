"""
Diagnostic script to test all LLM providers
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

def test_gemini():
    """Test Gemini API connection"""
    print("\n" + "="*60)
    print("Testing Gemini API")
    print("="*60)
    
    api_key = os.getenv("GEMINI_API", "")
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    
    print(f"API Key (first 20 chars): {api_key[:20] if api_key else 'NOT SET'}...")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    print(f"Model: {model}")
    
    if not api_key or api_key.strip() == "":
        print("❌ GEMINI_API key is not set!")
        return False
    
    # Check API key format
    if not api_key.startswith("AIzaSy"):
        print(f"⚠️  WARNING: Gemini API keys typically start with 'AIzaSy', yours starts with '{api_key[:6]}'")
        print("   This may be why the connection is failing.")
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        print("\nTesting generate content...")
        response = client.models.generate_content(
            model=model,
            contents=[{"parts": [{"text": "Say 'Hello, I am working!' in one line."}]}],
        )
        
        if response.text:
            print(f"✅ SUCCESS! Response: {response.text}")
            return True
        else:
            print("❌ FAILED: No text in response")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_mistral():
    """Test Mistral API connection"""
    print("\n" + "="*60)
    print("Testing Mistral API")
    print("="*60)
    
    api_key = os.getenv("MISTRAL_API_KEY", "")
    model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
    
    print(f"API Key (first 20 chars): {api_key[:20] if api_key else 'NOT SET'}...")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    print(f"Model: {model}")
    
    if not api_key or api_key.strip() == "":
        print("❌ MISTRAL_API_KEY is not set!")
        return False
    
    try:
        from mistralai.client.sdk import Mistral
        client = Mistral(api_key=api_key)
        
        print("\nTesting chat completion...")
        response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": "Say 'Hello, I am working!' in one line."}]
        )
        
        if response.choices[0].message:
            print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
            return True
        else:
            print("❌ FAILED: No message in response")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_ollama():
    """Test Ollama connection"""
    print("\n" + "="*60)
    print("Testing Ollama")
    print("="*60)
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
    
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    
    try:
        from ollama import Client
        client = Client(host=base_url, timeout=30)
        
        print("\nChecking Ollama server...")
        import httpx
        response = httpx.get(base_url, timeout=5)
        print(f"Server status: {response.status_code} - {response.text}")
        
        print(f"\nTesting generate with model: {model}...")
        response = client.generate(
            model=model,
            prompt="Say 'Hello, I am working!' in one line."
        )
        
        if response.response:
            print(f"✅ SUCCESS! Response: {response.response}")
            return True
        else:
            print("❌ FAILED: No response received")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("\nPossible issues:")
        print("  1. Ollama server is not running (run 'ollama serve')")
        print(f"  2. Model '{model}' is not installed (run 'ollama pull {model}')")
        return False


def main():
    print("\n" + "="*60)
    print("LLM Provider Diagnostic Tool")
    print("="*60)
    
    results = {
        "Gemini": test_gemini(),
        "Mistral": test_mistral(),
        "Ollama": test_ollama(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for provider, status in results.items():
        status_str = "✅ WORKING" if status else "❌ FAILED"
        print(f"{provider}: {status_str}")
    
    if not any(results.values()):
        print("\n⚠️  ALL PROVIDERS FAILED!")
        print("\nCommon solutions:")
        print("1. Check your API keys in .env file")
        print("2. Verify Gemini API key format (should start with 'AIzaSy')")
        print("3. Ensure Ollama is running and models are pulled")
        print("4. Check your internet connection for cloud APIs")
    
    print("\n")


if __name__ == "__main__":
    main()
