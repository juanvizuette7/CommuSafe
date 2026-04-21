"""Permisos específicos del módulo de incidentes."""

from rest_framework.permissions import BasePermission


class PuedeCrearIncidente(BasePermission):
    """Permite crear incidentes a residentes y vigilantes."""

    message = "Solo residentes y vigilantes pueden reportar incidentes."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.rol in {"RESIDENTE", "VIGILANTE"}
        )


class PuedeGestionarEstadoIncidente(BasePermission):
    """Permite cambiar estados a administradores y vigilantes."""

    message = "Solo administradores y vigilantes pueden cambiar el estado de un incidente"

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.rol in {"ADMINISTRADOR", "VIGILANTE"}
        )
