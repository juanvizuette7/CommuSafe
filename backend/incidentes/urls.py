"""Rutas base del módulo de incidentes."""

from django.urls import path

from .views import IncidentesRootAPIView


app_name = "incidentes"

urlpatterns = [
    path("", IncidentesRootAPIView.as_view(), name="root"),
]
