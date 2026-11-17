"""Roteamento principal do projeto Django."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("timetabling_api.urls")),
]
