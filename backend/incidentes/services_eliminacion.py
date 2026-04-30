"""Servicios de eliminacion trazable de incidentes."""

from django.db import transaction

from .models import IncidenteEliminado


@transaction.atomic
def eliminar_incidente_con_trazabilidad(incidente, usuario, motivo):
    """Registra la auditoria y elimina fisicamente el incidente."""

    registro = IncidenteEliminado.objects.create(
        incidente_id=incidente.id,
        titulo=incidente.titulo,
        eliminado_por=usuario,
        motivo=motivo.strip(),
    )
    incidente.delete()
    return registro
