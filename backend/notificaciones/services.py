"""Servicios de negocio para notificaciones internas y push."""

import logging
import os

from django.conf import settings
try:
    from pyfcm import FCMNotification
except ImportError:  # pragma: no cover - dependencia opcional en tiempo de ejecución
    FCMNotification = None

from usuarios.models import Usuario

from .models import Notificacion


logger = logging.getLogger(__name__)


class AudienciaAviso:
    TODOS = "TODOS"
    RESIDENTES = "RESIDENTES"
    VIGILANTES = "VIGILANTES"
    ADMINISTRADORES = "ADMINISTRADORES"

    CHOICES = (
        (TODOS, "Todos los usuarios activos"),
        (RESIDENTES, "Residentes activos"),
        (VIGILANTES, "Vigilantes activos"),
        (ADMINISTRADORES, "Administradores activos"),
    )


def _configuracion_push_disponible():
    if FCMNotification is None:
        return False
    valor = (settings.FCM_SERVER_KEY or "").strip()
    return bool(valor and "REEMPLAZAR" not in valor.upper() and os.path.exists(valor))


def _intentar_enviar_push(*, usuario, titulo, cuerpo, incidente=None):
    """Intenta enviar una notificación push sin romper el flujo principal."""

    try:
        if not usuario.fcm_token or not _configuracion_push_disponible():
            return False

        cliente = FCMNotification(service_account_file=settings.FCM_SERVER_KEY)
        cliente.notify(
            fcm_token=usuario.fcm_token,
            notification_title=titulo,
            notification_body=cuerpo,
            data_payload={
                "tipo": "notificacion_commusafe",
                "incidente_id": str(incidente.id) if incidente else "",
            },
        )
        return True
    except Exception as exc:
        logger.warning("No se pudo enviar notificación push a %s: %s", usuario.email, exc)
        return False


def _crear_registro_y_enviar_push(*, destinatario, titulo, cuerpo, tipo, incidente_relacionado=None):
    """Crea la notificación en base de datos y luego intenta enviarla por push."""

    enviada_push = _intentar_enviar_push(
        usuario=destinatario,
        titulo=titulo,
        cuerpo=cuerpo,
        incidente=incidente_relacionado,
    )
    return Notificacion.objects.create(
        destinatario=destinatario,
        titulo=titulo,
        cuerpo=cuerpo,
        tipo=tipo,
        incidente_relacionado=incidente_relacionado,
        enviada_push=enviada_push,
    )


def notificar_incidente_nuevo(incidente):
    """Notifica un incidente nuevo a los actores relevantes."""

    destinatarios = list(
        Usuario.objects.filter(activo=True, rol__in=[Usuario.Rol.VIGILANTE, Usuario.Rol.ADMINISTRADOR])
        .exclude(id=incidente.reportado_por_id)
        .distinct()
    )

    if incidente.prioridad == incidente.Prioridad.ALTA:
        residentes = Usuario.objects.filter(activo=True, rol=Usuario.Rol.RESIDENTE).exclude(
            id=incidente.reportado_por_id
        )
        destinatarios.extend(list(residentes))

    vistos = set()
    titulo = f"Nuevo incidente reportado: {incidente.titulo}"
    cuerpo = (
        f"Se registró un incidente de categoría {incidente.get_categoria_display().lower()} "
        f"con prioridad {incidente.get_prioridad_display().lower()}."
    )
    tipo = (
        Notificacion.Tipo.EMERGENCIA
        if incidente.prioridad == incidente.Prioridad.ALTA
        else Notificacion.Tipo.INCIDENTE_NUEVO
    )

    for destinatario in destinatarios:
        if destinatario.id in vistos:
            continue
        vistos.add(destinatario.id)
        _crear_registro_y_enviar_push(
            destinatario=destinatario,
            titulo=titulo,
            cuerpo=cuerpo,
            tipo=tipo,
            incidente_relacionado=incidente,
        )


def notificar_cambio_estado(incidente, estado_nuevo):
    """Notifica al residente reportante y al vigilante asignado sobre un cambio de estado."""

    destinatarios = [incidente.reportado_por]
    if incidente.atendido_por_id and incidente.atendido_por_id != incidente.reportado_por_id:
        destinatarios.append(incidente.atendido_por)

    titulo = f"Actualización del incidente: {incidente.titulo}"
    cuerpo = (
        f"El incidente ahora se encuentra en estado {dict(incidente.Estado.choices)[estado_nuevo].lower()}."
    )

    vistos = set()
    for destinatario in destinatarios:
        if destinatario.id in vistos or not destinatario.activo:
            continue
        vistos.add(destinatario.id)
        _crear_registro_y_enviar_push(
            destinatario=destinatario,
            titulo=titulo,
            cuerpo=cuerpo,
            tipo=Notificacion.Tipo.CAMBIO_ESTADO,
            incidente_relacionado=incidente,
        )


def notificar_aviso_admin(titulo, cuerpo):
    """Notifica un aviso administrativo a todos los usuarios activos del sistema."""

    return notificar_aviso_comunitario(
        titulo=titulo,
        cuerpo=cuerpo,
        audiencia=AudienciaAviso.TODOS,
        tipo=Notificacion.Tipo.AVISO_ADMIN,
    )


def _usuarios_por_audiencia(audiencia):
    queryset = Usuario.objects.filter(activo=True)
    if audiencia == AudienciaAviso.RESIDENTES:
        return queryset.filter(rol=Usuario.Rol.RESIDENTE)
    if audiencia == AudienciaAviso.VIGILANTES:
        return queryset.filter(rol=Usuario.Rol.VIGILANTE)
    if audiencia == AudienciaAviso.ADMINISTRADORES:
        return queryset.filter(rol=Usuario.Rol.ADMINISTRADOR)
    return queryset


def notificar_aviso_comunitario(
    *,
    titulo,
    cuerpo,
    audiencia=AudienciaAviso.TODOS,
    tipo=Notificacion.Tipo.AVISO_ADMIN,
):
    """Crea un aviso manual segmentado por audiencia y devuelve su resultado."""

    destinatarios = _usuarios_por_audiencia(audiencia)
    total = 0
    enviados_push = 0

    for destinatario in destinatarios.iterator():
        notificacion = _crear_registro_y_enviar_push(
            destinatario=destinatario,
            titulo=titulo,
            cuerpo=cuerpo,
            tipo=tipo,
        )
        total += 1
        if notificacion.enviada_push:
            enviados_push += 1

    return {
        "total_destinatarios": total,
        "push_enviadas": enviados_push,
        "audiencia": audiencia,
        "tipo": tipo,
    }
