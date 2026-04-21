"""Rutas de autenticación y administración de usuarios."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActualizarFCMTokenView,
    InicioSesionView,
    PerfilPropioView,
    RenovarTokenView,
    UsuarioViewSet,
)


app_name = "usuarios"

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("login/", InicioSesionView.as_view(), name="login"),
    path("refresh/", RenovarTokenView.as_view(), name="refresh"),
    path("perfil/", PerfilPropioView.as_view(), name="perfil"),
    path("fcm/", ActualizarFCMTokenView.as_view(), name="fcm"),
    path("", include(router.urls)),
]
