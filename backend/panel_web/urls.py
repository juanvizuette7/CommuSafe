"""Rutas del panel web administrativo."""

from django.urls import path

from .views import (
    dashboard,
    incidente_detalle,
    incidentes_lista,
    inicio,
    login_view,
    logout_view,
    usuario_toggle_activo,
    usuarios_lista,
)


app_name = "panel_web"

urlpatterns = [
    path("", inicio, name="inicio"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("incidentes/", incidentes_lista, name="incidentes_lista"),
    path("incidentes/<uuid:incidente_id>/", incidente_detalle, name="incidente_detalle"),
    path("usuarios/", usuarios_lista, name="usuarios_lista"),
    path("usuarios/<uuid:usuario_id>/toggle-activo/", usuario_toggle_activo, name="usuario_toggle_activo"),
]
