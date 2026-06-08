import os

from dotenv import load_dotenv

from sys_services.system_dirs import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

INITIAL_API_BASE_URL = os.getenv("SMARTDOCS_API_BASE_URL", "http://localhost:8000")

GOOGLE_PICKER_CONFIG = {
    "clientId": os.getenv("GOOGLE_CLOUD_SMARTDOCS_CLIENT_ID", ""),
    "apiKey": os.getenv("GOOGLE_CLOUD_SMARTDOCS_PICKER_CREDENTIALS", ""),
    "appId": os.getenv("GOOGLE_CLOUD_SMARTDOCS_APP_ID", ""),
    "scopes": os.getenv(
        "GOOGLE_PICKER_SCOPES",
        "https://www.googleapis.com/auth/drive.readonly",
    ),
    "apiBaseUrl": INITIAL_API_BASE_URL,
}
