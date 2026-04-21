"""Rutas del módulo de incidentes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IncidenteViewSet


app_name = "incidentes"

router = DefaultRouter()
router.register("", IncidenteViewSet, basename="incidente")

urlpatterns = [
    path("", include(router.urls)),
]
