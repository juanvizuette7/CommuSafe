"""Servicios de negocio del módulo de incidentes."""

from django.db import transaction
from django.utils import timezone

from notificaciones.services import crear_notificacion_incidente

from .models import HistorialEstado, Incidente


@transaction.atomic
def cambiar_estado_incidente(*, incidente, estado_nuevo, comentario, usuario):
    """Aplica una transición de estado y registra la trazabilidad."""

    estado_anterior = incidente.estado
    incidente.estado = estado_nuevo
    if not incidente.atendido_por_id or usuario.es_vigilante:
        incidente.atendido_por = usuario

    if estado_nuevo == Incidente.Estado.CERRADO:
        incidente.fecha_cierre = timezone.now()
        incidente.observaciones_cierre = comentario
    elif estado_nuevo == Incidente.Estado.RESUELTO:
        incidente.observaciones_cierre = comentario

    incidente.save()

    historial = HistorialEstado.objects.create(
        incidente=incidente,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        cambiado_por=usuario,
        comentario=comentario,
    )

    crear_notificacion_incidente(
        usuario=incidente.reportado_por,
        incidente=incidente,
        titulo=f"Actualización de incidente: {incidente.titulo}",
        mensaje=(
            f"Tu incidente ahora está en estado {incidente.get_estado_display().lower()}. "
            f"Comentario: {comentario}"
        ),
    )

    return incidente, historial
