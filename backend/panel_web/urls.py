"""Rutas del panel web administrativo."""

from django.urls import path

from .views import (
    avisos_comunitarios,
    dashboard,
    incidente_detalle,
    incidentes_lista,
    inicio,
    login_view,
    logout_view,
    panel_notificacion_leer,
    panel_notificaciones,
    reset_confirmar,
    reset_solicitar,
    usuario_cambiar_rol,
    usuario_crear,
    usuario_editar,
    usuario_eliminar,
    usuario_toggle_activo,
    usuarios_lista,
)


app_name = "panel_web"

urlpatterns = [
    path("", inicio, name="inicio"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("reset/", reset_solicitar, name="reset_solicitar"),
    path("reset/<str:token>/", reset_confirmar, name="reset_confirmar"),
    path("dashboard/", dashboard, name="dashboard"),
    path("notificaciones/", panel_notificaciones, name="panel_notificaciones"),
    path("panel/notificaciones/", panel_notificaciones, name="panel_notificaciones_alias"),
    path("notificaciones/<uuid:id>/leer/", panel_notificacion_leer, name="panel_notificacion_leer"),
    path("panel/notificaciones/<uuid:id>/leer/", panel_notificacion_leer, name="panel_notificacion_leer_alias"),
    path("incidentes/", incidentes_lista, name="incidentes_lista"),
    path("incidentes/<uuid:incidente_id>/", incidente_detalle, name="incidente_detalle"),
    path("avisos/", avisos_comunitarios, name="avisos"),
    path("usuarios/", usuarios_lista, name="usuarios_lista"),
    path("usuarios/crear/", usuario_crear, name="usuario_crear"),
    path("usuarios/<uuid:usuario_id>/editar/", usuario_editar, name="usuario_editar"),
    path("usuarios/<uuid:usuario_id>/cambiar-rol/", usuario_cambiar_rol, name="usuario_cambiar_rol"),
    path("usuarios/<uuid:usuario_id>/eliminar/", usuario_eliminar, name="usuario_eliminar"),
    path("usuarios/<uuid:usuario_id>/toggle-activo/", usuario_toggle_activo, name="usuario_toggle_activo"),
]
