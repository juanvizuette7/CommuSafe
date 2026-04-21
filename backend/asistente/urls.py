"""Rutas base del módulo de asistente virtual."""

from django.urls import path

from .views import AsistenteRootAPIView


app_name = "asistente"

urlpatterns = [
    path("", AsistenteRootAPIView.as_view(), name="root"),
]
