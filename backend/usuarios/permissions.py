"""Permisos personalizados para la app de usuarios."""

from rest_framework.permissions import BasePermission


class _RolBasePermission(BasePermission):
    mensaje_autenticacion = "Debes iniciar sesión para realizar esta acción."
    mensaje_rol = "No tienes permisos suficientes para realizar esta acción."
    roles_permitidos = set()

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            self.message = self.mensaje_autenticacion
            return False

        if usuario.rol not in self.roles_permitidos:
            self.message = self.mensaje_rol
            return False

        return True


class EsAdministrador(_RolBasePermission):
    message = "Solo los administradores pueden realizar esta acción."
    mensaje_rol = "Solo los administradores pueden realizar esta acción."
    roles_permitidos = {"ADMINISTRADOR"}


class EsVigilante(_RolBasePermission):
    message = "Solo el personal de vigilancia puede realizar esta acción."
    mensaje_rol = "Solo el personal de vigilancia puede realizar esta acción."
    roles_permitidos = {"VIGILANTE"}


class EsResidente(_RolBasePermission):
    message = "Solo los residentes pueden realizar esta acción."
    mensaje_rol = "Solo los residentes pueden realizar esta acción."
    roles_permitidos = {"RESIDENTE"}


class EsAdministradorOVigilante(_RolBasePermission):
    message = "Solo administradores o vigilantes pueden realizar esta acción."
    mensaje_rol = "Solo administradores o vigilantes pueden realizar esta acción."
    roles_permitidos = {"ADMINISTRADOR", "VIGILANTE"}
