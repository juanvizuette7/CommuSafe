"""Rutas base del módulo de notificaciones."""

from django.urls import path

from .views import NotificacionesRootAPIView


app_name = "notificaciones"

urlpatterns = [
    path("", NotificacionesRootAPIView.as_view(), name="root"),
]
