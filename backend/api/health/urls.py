from django.urls import path

from backend.api.health.views import APIHealthView

urlpatterns = [
    path("", APIHealthView.as_view(), name="health"),
]