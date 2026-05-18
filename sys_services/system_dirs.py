from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:8000"

ROOT_DIR = Path(__file__).resolve().parents[1]

BASE_FE_DIR = ROOT_DIR / "frontend"
BASE_BE_DIR = ROOT_DIR / "backend"
LOGS_DIR = ROOT_DIR / "docs" / "logs"