import os

from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

CHUNKING_CONFIG = {
    "chunk_size": int(os.getenv("CHUNK_SIZE", 1000)),
    "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", 200)),
}