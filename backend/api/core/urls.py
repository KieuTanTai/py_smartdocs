from django.urls import path

from backend.api.core.views import CoreSearchView

urlpatterns = [
    path("search/", CoreSearchView.as_view(), name="core-search"),
]
