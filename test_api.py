import requests
import json

# Test sending a message
url = "http://localhost:8000/api/conversations/019efa08-6b98-795b-86ab-af0d32323d56/messages/"
payload = {
    "user_input": "yêu cầu trong báo cáo là gì",
    "provider_name": "mistral",
    "model_name": "mistral-large-latest"
}

print("=== TESTING MISTRAL API ===")
response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"\nResponse:")
data = response.json()
print(f"Assistant: {data.get('assistant')[:200]}...")
print(f"Used Mock: {data.get('used_mock')}")
print(f"Provider: {data.get('metrics', {}).get('provider')}")
print(f"Model: {data.get('metrics', {}).get('model')}")
print(f"Total Time: {data.get('metrics', {}).get('total_ms')}ms")
