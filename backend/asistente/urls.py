"""Rutas del módulo de asistente virtual."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatAsistenteView, ChatHealthView, ConversacionAsistenteViewSet


app_name = "asistente"

router = DefaultRouter()
router.register("conversaciones", ConversacionAsistenteViewSet, basename="conversacion")

urlpatterns = [
    path("", include(router.urls)),
    path("chat/", ChatAsistenteView.as_view(), name="chat"),
    path("health/", ChatHealthView.as_view(), name="health"),
]
