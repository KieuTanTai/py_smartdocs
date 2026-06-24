import httpx

url = "http://localhost:8000/api/conversations/"
payload = {
    "title": "Test",
    "provider": "gemini",
    "model": "gemini-3.1-flash-lite",
    "system_prompt": "",
    "document_ids": [],
    "mode": "normal"
}

try:
    response = httpx.post(url, json=payload, timeout=10.0)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
