"""Rutas del módulo de asistente virtual."""

from django.urls import path

from .views import ChatAsistenteView, ChatHealthView


app_name = "asistente"

urlpatterns = [
    path("chat/", ChatAsistenteView.as_view(), name="chat"),
    path("health/", ChatHealthView.as_view(), name="health"),
]
