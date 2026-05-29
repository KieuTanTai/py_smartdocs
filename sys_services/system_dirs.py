from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:8000"

ROOT_DIR = Path(__file__).resolve().parents[1]

BASE_FE_DIR = ROOT_DIR / "frontend"
BASE_BE_DIR = ROOT_DIR / "backend"
LOGS_DIR = ROOT_DIR / "docs" / "logs"
METADATA_DIR = BASE_BE_DIR / "metadata"
METADATA_DOCS_DIR = METADATA_DIR / "docs"
METADATA_IMAGE_DIR = METADATA_DIR / "images"
METADATA_TEMP_DIR = METADATA_DIR / "temp"