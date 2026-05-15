import os

from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")
INITIAL_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
CLUSTER_CONFIG = {
    "collection_name": os.getenv(
        "CLUSTER_GLOBAL_SEARCH_COLLECTION", "smartdocsai_documents"
    ),
    "collection_name_multitenancy": os.getenv(
        "CLUSTER_MULTITENANCY_COLLECTION", "smartdocsai_documents_multitenancy"
    ),
    "node": os.getenv("CLUSTER_NODE", ""),
    "endpoint": os.getenv("CLUSTER_ENDPOINT", INITIAL_QDRANT_URL),
    "api_key": os.getenv("CLUSTER_API_KEY", ""),
}
