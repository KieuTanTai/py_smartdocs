import os

from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")
endpoint = os.getenv("REDIS_ENDPOINT", "redis://localhost:6379")
host = endpoint.split("://")[-1].split(":")[0]
port = int(endpoint.split(":")[-1])
REDIS_CONFIG = {
    "endpoint": endpoint,
    "host": host,
    "port": port,
    "db": int(os.getenv("REDIS_DB", 0)),
    "celery_broker_url": os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    "celery_result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    "api_key": os.getenv("CLUSTER_API_KEY", ""),
}
