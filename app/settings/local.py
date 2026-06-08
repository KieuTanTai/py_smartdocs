import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# ── 1. Sentry (Error Tracking) ────────────────────────────────────────────────
# Initialise as early as possible so all modules are instrumented.
_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.httpx import HttpxIntegration

        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[
                DjangoIntegration(),
                HttpxIntegration(),
            ],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
            environment=os.getenv("ENVIRONMENT", "development"),
        )
        logging.getLogger("sentry_sdk").info("Sentry initialised")
    except ImportError:
        pass   # sentry-sdk not installed

# ── 2. Celery (Background Tasks) ───────────────────────────────────────────────
_celery_app = None
_celery_available = False
_redis_broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
_redis_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

try:
    import celery
    _celery_app = celery.Celery(
        "smartdocs",
        broker=_redis_broker,
        backend=_redis_backend,
        include=["backend.apps.tasks"],
    )
    _celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_routes={
            "backend.apps.tasks.index_document": {"queue": "indexing"},
            "backend.apps.tasks.bulk_index_documents": {"queue": "indexing"},
        },
        task_default_queue="default",
    )
    _celery_available = True
    logging.getLogger("celery").info("Celery app initialised")
except ImportError:
    logging.warning("Celery not installed; background tasks unavailable.")


def get_celery_app():
    """Return the Celery app instance (or None if unavailable)."""
    return _celery_app


# ── 3. Django Settings ─────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-secret-key")
DEBUG = os.getenv("DEBUG", "0") == "1"

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "corsheaders",
    "backend.apps.services.chat",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

# ── CORS Configuration ──────────────────────────────────────────────────────────
# Allow frontend (Shiny) running on a different port in development.
# In production, restrict to your actual frontend domain.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

# Allow Authorization header (needed for JWT Bearer token)
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-requested-with",
]

# Allow all methods for development; tighten in production
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# ── REST Framework Configuration ───────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "UNAUTHENTICATED_USER": None,
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"
ASGI_APPLICATION = "app.asgi.application"

# ── Database Configuration ───────────────────────────────────────────────────────
# Falls back to SQLite if DB_ENGINE is not set or unavailable.
db_engine = os.getenv("DB_ENGINE", "django.db.backends.mysql")
if db_engine == "django.db.backends.mariadb":
    db_engine = "django.db.backends.mysql"

db_name = os.getenv("DB_NAME", "py_smartdocs")
db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "change-me")
db_host = os.getenv("DB_HOST", "127.0.0.1")
db_port = os.getenv("DB_PORT", "3306")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Attempt MariaDB if DB_ENGINE is explicitly set and MySQL client is available.
if os.getenv("DB_ENGINE") and os.getenv("DB_ENGINE") != "django.db.backends.sqlite3":
    try:
        import MySQLdb  # noqa: F401 — only to verify the driver is available
        DATABASES = {
            "default": {
                "ENGINE": db_engine,
                "NAME": db_name,
                "USER": db_user,
                "PASSWORD": db_password,
                "HOST": db_host,
                "PORT": db_port,
                "OPTIONS": {
                    "charset": "utf8mb4",
                    "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                },
            }
        }
    except ImportError:
        pass   # MySQL driver not installed; keep SQLite

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Static & Media Files ────────────────────────────────────────────────────────
STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "storage" / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
