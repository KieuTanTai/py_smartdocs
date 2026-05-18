import os

from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

OLLAMA_CONFIG = {
    "base_url": os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434"),
    "model": os.getenv("OLLAMA_MODEL", "llama3"),
    "timeout_seconds": float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60.0")),
}
