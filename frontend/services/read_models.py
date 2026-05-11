import os
from dotenv import load_dotenv

from services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

DEFAULT_MODELS = [
    "auto",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "ollama:llama3",
    "ollama:mistral",
]

LIST_MODELS = os.getenv("MODEL_LIST", ",".join(DEFAULT_MODELS)).split(",")
