from django.urls import path

from backend.api.providers.views import ProviderListView, ProviderTestView

urlpatterns = [
    path("", ProviderListView.as_view(), name="providers"),
    path("test/", ProviderTestView.as_view(), name="providers-test"),
]
