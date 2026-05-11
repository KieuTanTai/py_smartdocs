import sys
from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:8000"

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

BASE_DIR = ROOT_DIR / "frontend"
