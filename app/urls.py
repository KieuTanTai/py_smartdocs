from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from backend.api.gateway import urlpatterns as api_urls

urlpatterns = api_urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
