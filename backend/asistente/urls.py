"""Rutas del módulo de asistente virtual."""

from django.urls import path

from .views import ChatAsistenteView


app_name = "asistente"

urlpatterns = [
    path("chat/", ChatAsistenteView.as_view(), name="chat"),
]
