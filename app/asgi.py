"""
ASGI entry point for SmartDocs Django application.
Used by uvicorn to serve the Django app.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")
application = get_asgi_application()

# Also expose celery app for any ASGI workers that need it
from app.settings.local import get_celery_app
