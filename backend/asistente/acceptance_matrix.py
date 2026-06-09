"""Matriz verificable de aceptación del motor local de CommuBot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AcceptanceCase:
    categoria: str
    mensaje: str
    rol: str = "RESIDENTE"
    acciones_aceptadas: tuple[str, ...] = ("answer",)
    intenciones_aceptadas: tuple[str, ...] = ()


ACCEPTANCE_CASES = (
    AcceptanceCase(
        "conocida",
        "Como reporto un incidente?",
        acciones_aceptadas=("answer",),
        intenciones_aceptadas=("reportar_incidente",),
    ),
    AcceptanceCase(
        "conocida",
        "Donde veo las notificaciones?",
        acciones_aceptadas=("answer",),
        intenciones_aceptadas=("navegacion_app",),
    ),
    AcceptanceCase(
        "variacion_nueva",
        "parce no puedo entrar a la cuenta que hago",
        acciones_aceptadas=("answer",),
        intenciones_aceptadas=("acceso_sesion",),
    ),
    AcceptanceCase(
        "variacion_nueva",
        "quiero saber como va el caso que reporte",
        acciones_aceptadas=("answer", "clarify"),
        intenciones_aceptadas=("seguimiento_incidente",),
    ),
    AcceptanceCase(
        "error_ortografico",
        "komo reporto un insidente",
        acciones_aceptadas=("answer",),
        intenciones_aceptadas=("reportar_incidente",),
    ),
    AcceptanceCase(
        "error_ortografico",
        "no me yegan las notificasiones",
        acciones_aceptadas=("answer", "clarify"),
        intenciones_aceptadas=("gestion_notificaciones", "navegacion_app"),
    ),
    AcceptanceCase(
        "ambigua",
        "musica alta",
        acciones_aceptadas=("clarify",),
    ),
    AcceptanceCase(
        "ambigua",
        "Tengo una duda con un reporte y una alerta",
        acciones_aceptadas=("clarify", "fallback_allowed"),
    ),
    AcceptanceCase(
        "fuera_dominio",
        "quien gano el partido de futbol ayer",
        acciones_aceptadas=("safe",),
        intenciones_aceptadas=("sin_intencion_confiable",),
    ),
    AcceptanceCase(
        "fuera_dominio",
        "explicame como cocinar pasta",
        acciones_aceptadas=("safe",),
        intenciones_aceptadas=("sin_intencion_confiable",),
    ),
    AcceptanceCase(
        "desconocida_dominio",
        "procedimiento biometrico de porteria para QR temporal",
        acciones_aceptadas=("fallback_allowed",),
    ),
)


def evaluate_acceptance_case(case, result):
    action_ok = result.get("action") in case.acciones_aceptadas
    intent_ok = not case.intenciones_aceptadas or result.get("intent") in case.intenciones_aceptadas
    return {
        "categoria": case.categoria,
        "mensaje": case.mensaje,
        "rol": case.rol,
        "accion": result.get("action", ""),
        "intencion": result.get("intent", ""),
        "metodo": result.get("method", ""),
        "confianza": result.get("confidence", 0),
        "cumple": action_ok and intent_ok,
    }
