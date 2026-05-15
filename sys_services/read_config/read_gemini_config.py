import os
from dotenv import load_dotenv
from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

GEMINI_EMBEDDING_CONFIG = {
    "model": os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2"),
    "apiKey": os.getenv("GEMINI_API", ""),
}
