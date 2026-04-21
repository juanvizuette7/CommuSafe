"""Servicios internos para notificaciones."""

from .models import Notificacion


def crear_notificacion_incidente(*, usuario, incidente, titulo, mensaje):
    """Genera una notificación interna asociada a un incidente."""

    return Notificacion.objects.create(
        usuario=usuario,
        incidente=incidente,
        titulo=titulo,
        mensaje=mensaje,
        tipo=Notificacion.Tipo.INCIDENTE,
    )
