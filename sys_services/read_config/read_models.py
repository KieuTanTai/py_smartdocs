import os
from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")

LIST_MODELS = os.getenv("MODEL_LIST", "gemini, mistral, ollama").split(", ")