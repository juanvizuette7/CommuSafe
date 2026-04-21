"""Rutas del panel web."""

from django.urls import path

from .views import InicioPanelView


app_name = "panel_web"

urlpatterns = [
    path("", InicioPanelView.as_view(), name="inicio"),
]
