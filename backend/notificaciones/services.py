"""Servicios de negocio para notificaciones internas y push."""

import base64
import json
import logging
import os

from django.conf import settings

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:  # pragma: no cover - dependencia opcional en tiempo de ejecucion
    firebase_admin = None
    credentials = None
    messaging = None

from usuarios.models import Usuario

from .models import Notificacion


logger = logging.getLogger(__name__)
_firebase_app = None


class AudienciaAviso:
    TODOS = "TODOS"
    RESIDENTES = "RESIDENTES"
    VIGILANTES = "VIGILANTES"
    ADMINISTRADORES = "ADMINISTRADORES"
    ESPECIFICOS = "ESPECIFICOS"

    CHOICES = (
        (TODOS, "Todos los usuarios activos"),
        (RESIDENTES, "Residentes activos"),
        (VIGILANTES, "Vigilantes activos"),
        (ADMINISTRADORES, "Administradores activos"),
        (ESPECIFICOS, "Usuarios seleccionados"),
    )


def _configuracion_push_disponible():
    if firebase_admin is None or credentials is None or messaging is None:
        return False
    json_base64 = (getattr(settings, "FIREBASE_CREDENTIALS_JSON_BASE64", "") or "").strip()
    json_directo = (getattr(settings, "FIREBASE_CREDENTIALS_JSON", "") or "").strip()
    ruta = (settings.FIREBASE_CREDENTIALS_PATH or "").strip()
    if json_base64 or json_directo:
        return True
    return bool(ruta and "REEMPLAZAR" not in ruta.upper() and os.path.exists(ruta))


def _crear_credencial_firebase():
    json_base64 = (getattr(settings, "FIREBASE_CREDENTIALS_JSON_BASE64", "") or "").strip()
    json_directo = (getattr(settings, "FIREBASE_CREDENTIALS_JSON", "") or "").strip()
    if json_base64:
        datos = json.loads(base64.b64decode(json_base64).decode("utf-8"))
        return credentials.Certificate(datos)
    if json_directo:
        return credentials.Certificate(json.loads(json_directo))
    return credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)


def _obtener_firebase_app():
    """Inicializa Firebase Admin una sola vez y reutiliza la app."""

    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        _firebase_app = firebase_admin.get_app()
    except ValueError:
        credencial = _crear_credencial_firebase()
        _firebase_app = firebase_admin.initialize_app(credencial)
    return _firebase_app


def _intentar_enviar_push(*, usuario, titulo, cuerpo, incidente=None):
    """Intenta enviar una notificacion push sin romper el flujo principal."""

    try:
        if not usuario.fcm_token or not _configuracion_push_disponible():
            return False

        mensaje = messaging.Message(
            token=usuario.fcm_token,
            notification=messaging.Notification(title=titulo, body=cuerpo),
            data={
                "tipo": "notificacion_commusafe",
                "incidente_id": str(incidente.id) if incidente else "",
            },
        )
        messaging.send(mensaje, app=_obtener_firebase_app())
        return True
    except Exception as exc:
        logger.warning("No se pudo enviar notificacion push a %s: %s", usuario.email, exc)
        return False


def _crear_registro_y_enviar_push(*, destinatario, titulo, cuerpo, tipo, incidente_relacionado=None):
    """Crea la notificacion en base de datos y luego intenta enviarla por push."""

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
        f"Se registro un incidente de categoria {incidente.get_categoria_display().lower()} "
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

    titulo = f"Actualizacion del incidente: {incidente.titulo}"
    cuerpo = f"El incidente ahora se encuentra en estado {dict(incidente.Estado.choices)[estado_nuevo].lower()}."

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


def usuarios_disponibles_para_aviso(usuario):
    """Devuelve usuarios activos que el solicitante puede elegir como destinatarios."""

    queryset = Usuario.objects.filter(activo=True).order_by("rol", "nombre", "apellido", "email")
    if usuario.es_vigilante:
        queryset = queryset.filter(rol=Usuario.Rol.RESIDENTE)
    return queryset


def notificar_aviso_comunitario(
    *,
    titulo,
    cuerpo,
    audiencia=AudienciaAviso.TODOS,
    tipo=Notificacion.Tipo.AVISO_ADMIN,
    destinatarios=None,
):
    """Crea un aviso manual segmentado por audiencia y devuelve su resultado."""

    destinatarios_queryset = (
        Usuario.objects.filter(id__in=[usuario.id for usuario in destinatarios], activo=True)
        if destinatarios is not None
        else _usuarios_por_audiencia(audiencia)
    )
    total = 0
    enviados_push = 0
    vistos = set()

    for destinatario in destinatarios_queryset.iterator():
        if destinatario.id in vistos:
            continue
        vistos.add(destinatario.id)
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
