import os

from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

INITIAL_API_BASE_URL = os.getenv("SMARTDOCS_API_BASE_URL", "http://localhost:8000")

MISTRAL_CONFIG = {
    "api_key": os.getenv("MISTRAL_API_KEY", ""),
    "ocr_model": os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest"),
    "embedding_model": os.getenv("MISTRAL_EMBEDDING_MODEL", "mistral-embed"),
    "model": os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
    "confidence_scores_granularity": os.getenv(
        "MISTRAL_CONFIDENCE_SCORES_GRANULARITY", "word"
    ),
    "timeout_seconds": int(os.getenv("MISTRAL_TIMEOUT_SECONDS", "60")),
    "document_type": os.getenv("MISTRAL_DOCUMENT_TYPE", "UPLOAD_FILES"),
    "api_base_url": INITIAL_API_BASE_URL,
}
