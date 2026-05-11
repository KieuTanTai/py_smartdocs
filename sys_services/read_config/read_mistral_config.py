import os

from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

INITIAL_API_BASE_URL = os.getenv("SMARTDOCS_API_BASE_URL", "http://localhost:8000")

MISTRAL_CONFIG = {
    "apiKey": os.getenv("MISTRAL_API_KEY", ""),
    "model": os.getenv("MISTRAL_MODEL", "mistral-ocr-latest"),
    "confidenceScoresGranularity": os.getenv(
        "MISTRAL_CONFIDENCE_SCORES_GRANULARITY", "word"
    ),
    "timeoutSeconds": int(os.getenv("MISTRAL_TIMEOUT_SECONDS", "60")),
    "documentType": os.getenv("MISTRAL_DOCUMENT_TYPE", "UPLOAD_FILES"),
    "apiBaseUrl": INITIAL_API_BASE_URL,
}
