"""Rutas de autenticación y administración de usuarios."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActualizarFCMTokenView,
    ConfirmarResetView,
    InicioSesionView,
    PerfilPropioView,
    RenovarTokenView,
    SolicitarResetView,
    UsuarioViewSet,
)


app_name = "usuarios"

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("login/", InicioSesionView.as_view(), name="login"),
    path("refresh/", RenovarTokenView.as_view(), name="refresh"),
    path("reset-solicitar/", SolicitarResetView.as_view(), name="reset_solicitar"),
    path("reset-confirmar/", ConfirmarResetView.as_view(), name="reset_confirmar"),
    path("perfil/", PerfilPropioView.as_view(), name="perfil"),
    path("fcm/", ActualizarFCMTokenView.as_view(), name="fcm"),
    path("", include(router.urls)),
]
