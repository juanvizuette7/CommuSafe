"""Repositorio de conocimiento administrable para el motor local."""

from __future__ import annotations

from django.core.exceptions import AppRegistryNotReady
from django.db import OperationalError, ProgrammingError
from django.db.models import Max
from django.utils import timezone

from .local_knowledge import FAQEntry, FAQ_ENTRIES


ENTRADAS_ESTATICAS_CONTROLADAS = tuple(entrada for entrada in FAQ_ENTRIES if entrada.is_active())


def _entrada_modelo_a_faq(entrada):
    actualizado = entrada.fecha_actualizacion.date().isoformat() if entrada.fecha_actualizacion else ""
    return FAQEntry(
        id=entrada.codigo,
        intent=entrada.subintencion or entrada.codigo,
        category=entrada.categoria,
        question=entrada.pregunta,
        answer=entrada.respuesta,
        keywords=tuple(entrada.palabras_clave or []),
        variations=tuple(entrada.variaciones or []),
        allowed_roles=tuple(entrada.roles_permitidos or []),
        verified=True,
        updated_at=actualizado,
        valid_from=entrada.vigente_desde.isoformat() if entrada.vigente_desde else "",
        valid_until=entrada.vigente_hasta.isoformat() if entrada.vigente_hasta else "",
        maintainer_role="ADMINISTRADOR",
        source=entrada.fuente or "Base de conocimiento administrable CommuSafe",
        change_trace=(f"Version administrada {entrada.version}.",),
        main_intent_override=entrada.intencion_principal,
    )


def obtener_snapshot_conocimiento():
    """Combina respaldo estatico con entradas aprobadas de base de datos."""

    try:
        from .models import EntradaConocimiento

        fecha = timezone.localdate()
        queryset = EntradaConocimiento.objects.all()
        administrables = list(queryset.order_by("codigo"))
        agregado = queryset.aggregate(max_actualizacion=Max("fecha_actualizacion"), max_version=Max("version"))
    except (AppRegistryNotReady, OperationalError, ProgrammingError):
        return ENTRADAS_ESTATICAS_CONTROLADAS, "static"

    codigos_administrados = {entrada.codigo for entrada in administrables}
    por_codigo = {
        entry.id: entry
        for entry in ENTRADAS_ESTATICAS_CONTROLADAS
        if entry.id not in codigos_administrados
    }
    for entrada in administrables:
        if entrada.esta_publicable(fecha):
            por_codigo[entrada.codigo] = _entrada_modelo_a_faq(entrada)

    max_actualizacion = agregado["max_actualizacion"]
    revision = (
        f"db:{len(administrables)}:"
        f"{max_actualizacion.isoformat() if max_actualizacion else 'sin-fecha'}:"
        f"{agregado['max_version'] or 0}"
    )
    return tuple(por_codigo.values()), revision
