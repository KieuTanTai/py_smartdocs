from django.urls import path

from backend.api.urls import HealthView
urlpatterns = [
    path('api/health/', HealthView.as_view(), name='health'),
    
]