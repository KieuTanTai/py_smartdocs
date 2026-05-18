import os
from dotenv import load_dotenv
from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

GEMINI_EMBEDDING_CONFIG = {
    "api_key": os.getenv("GEMINI_API", ""),
    "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "embedding_model": os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2"),
    "timeout_seconds": int(os.getenv("GEMINI_TIMEOUT_SECONDS", "60")),
}
