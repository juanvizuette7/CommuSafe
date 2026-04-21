"""Rutas del módulo de notificaciones."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificacionViewSet


app_name = "notificaciones"

router = DefaultRouter()
router.register("", NotificacionViewSet, basename="notificacion")

urlpatterns = [
    path("", include(router.urls)),
]
