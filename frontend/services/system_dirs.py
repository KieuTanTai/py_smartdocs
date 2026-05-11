import sys
from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:8000"

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

ROOT_DIR = BASE_DIR.parent
