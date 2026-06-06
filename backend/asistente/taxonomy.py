"""Taxonomia profesional de intenciones principales de CommuBot.

Las FAQ conservan su subintencion especifica, pero el clasificador y las
metricas trabajan con un conjunto menor de intenciones principales. Esto evita
clases excesivamente pequenas sin perder respuestas preparadas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MainIntent:
    id: str
    label: str
    description: str
    faq_ids: tuple[str, ...]


MAIN_INTENTS: tuple[MainIntent, ...] = (
    MainIntent(
        "acceso_sesion",
        "Acceso y sesion",
        "Inicio de sesion, recuperacion de acceso, cierre de sesion y problemas de conexion.",
        ("uso_001", "uso_002", "uso_012", "uso_014"),
    ),
    MainIntent(
        "perfil_preferencias",
        "Perfil y preferencias",
        "Actualizacion de datos, foto, accesibilidad, apariencia e idioma.",
        ("uso_008", "uso_009", "uso_010", "uso_011"),
    ),
    MainIntent(
        "navegacion_app",
        "Navegacion de la aplicacion",
        "Ubicacion y comportamiento de modulos generales de la aplicacion.",
        ("uso_006", "uso_007", "uso_015"),
    ),
    MainIntent(
        "reportar_incidente",
        "Registro de incidentes",
        "Creacion, redaccion y evidencias de un nuevo reporte.",
        ("uso_003", "uso_005", "inc_011", "inc_013"),
    ),
    MainIntent(
        "seguimiento_incidente",
        "Seguimiento de incidentes",
        "Estados, historial, casos repetidos, contacto y eliminacion trazable.",
        (
            "uso_004",
            "inc_006",
            "inc_007",
            "inc_008",
            "inc_009",
            "inc_010",
            "inc_012",
            "inc_014",
            "inc_015",
        ),
    ),
    MainIntent(
        "clasificacion_incidente",
        "Clasificacion de incidentes",
        "Categorias y prioridad automatica de los reportes.",
        ("inc_001", "inc_002", "inc_003", "inc_004", "inc_005"),
    ),
    MainIntent(
        "gestion_notificaciones",
        "Gestion de notificaciones",
        "Recepcion, lectura, push y segmentacion de alertas.",
        ("not_001", "not_002", "not_006", "not_007", "not_008", "not_009", "not_012"),
    ),
    MainIntent(
        "gestion_avisos",
        "Gestion de avisos",
        "Avisos administrativos, destinatarios, recurrencia y visualizacion.",
        ("not_003", "not_004", "not_005", "not_010", "not_011"),
    ),
    MainIntent(
        "emergencias",
        "Emergencias",
        "Orientacion inmediata ante riesgos para la vida o integridad.",
        ("seg_001", "seg_002", "seg_003", "seg_007", "seg_010", "seg_012"),
    ),
    MainIntent(
        "seguridad_control",
        "Seguridad y control",
        "Novedades de vigilancia, accesos, personas, vehiculos y evidencia segura.",
        ("seg_004", "seg_005", "seg_006", "seg_008", "seg_009", "seg_011"),
    ),
    MainIntent(
        "tramites_administrativos",
        "Tramites administrativos",
        "Horarios, pagos, documentos, datos de contacto y canales administrativos.",
        ("adm_001", "adm_002", "adm_003", "adm_004", "adm_005", "adm_012"),
    ),
    MainIntent(
        "administracion_panel",
        "Administracion del sistema",
        "Gestion de usuarios, roles, dashboard, exportaciones y auditoria.",
        ("adm_006", "adm_007", "adm_008", "adm_009", "adm_010", "adm_011"),
    ),
    MainIntent(
        "convivencia_conflictos",
        "Convivencia y conflictos",
        "Ruido, conflictos, reuniones, comunicacion y situaciones recurrentes.",
        ("conv_001", "conv_002", "conv_003", "conv_004", "conv_007", "conv_008", "conv_012"),
    ),
    MainIntent(
        "convivencia_entorno",
        "Convivencia y entorno comun",
        "Uso respetuoso, horarios, reservas, limpieza, danos y convivencia en espacios compartidos.",
        (
            "conv_005",
            "conv_006",
            "conv_009",
            "conv_010",
            "conv_011",
            "zc_001",
            "zc_002",
            "zc_003",
            "zc_004",
        ),
    ),
    MainIntent(
        "visitantes_ingresos",
        "Visitantes e ingresos",
        "Autorizacion y control de visitantes, domiciliarios, proveedores y vehiculos.",
        ("vis_001", "vis_002", "vis_003", "vis_004", "vis_005", "vis_006"),
    ),
    MainIntent(
        "parqueaderos_vehiculos",
        "Parqueaderos y vehiculos",
        "Bloqueos, ocupacion, danos y circulacion en parqueaderos.",
        ("parq_001", "parq_002", "parq_003", "parq_004"),
    ),
    MainIntent(
        "mascotas",
        "Mascotas",
        "Convivencia, limpieza, extravio y riesgos relacionados con mascotas.",
        ("mas_001", "mas_002", "mas_003", "mas_004"),
    ),
    MainIntent(
        "mantenimiento_infraestructura",
        "Mantenimiento e infraestructura",
        "Fallas, danos y mantenimiento de elementos comunes.",
        ("mant_001", "mant_002", "mant_003", "mant_004", "mant_005"),
    ),
    MainIntent(
        "funcionamiento_asistente",
        "Funcionamiento del asistente",
        "Alcance, limites, modo hibrido, aclaraciones y metricas del asistente.",
        ("asis_001", "asis_002", "asis_003", "asis_004", "asis_006", "asis_007"),
    ),
    MainIntent(
        "privacidad_conversaciones",
        "Privacidad y conversaciones",
        "Persistencia y privacidad del historial conversacional.",
        ("uso_013", "asis_005"),
    ),
)


MAIN_INTENT_BY_ID = {intent.id: intent for intent in MAIN_INTENTS}
FAQ_TO_MAIN_INTENT = {
    faq_id: intent.id
    for intent in MAIN_INTENTS
    for faq_id in intent.faq_ids
}


def get_main_intent_id(faq_id: str) -> str:
    """Devuelve la intencion principal asociada a una FAQ."""

    return FAQ_TO_MAIN_INTENT.get(faq_id, "sin_intencion_confiable")


def taxonomy_summary() -> dict[str, object]:
    """Resumen verificable de la taxonomia principal."""

    sizes = {intent.id: len(intent.faq_ids) for intent in MAIN_INTENTS}
    return {
        "intenciones_principales": len(MAIN_INTENTS),
        "faq_clasificadas": len(FAQ_TO_MAIN_INTENT),
        "min_faq_por_intencion": min(sizes.values()) if sizes else 0,
        "max_faq_por_intencion": max(sizes.values()) if sizes else 0,
        "faq_por_intencion": sizes,
    }


def validate_taxonomy(faq_ids: set[str]) -> list[str]:
    """Valida cobertura completa y ausencia de FAQ asignadas varias veces."""

    errors: list[str] = []
    assigned = [faq_id for intent in MAIN_INTENTS for faq_id in intent.faq_ids]
    duplicates = sorted({faq_id for faq_id in assigned if assigned.count(faq_id) > 1})
    missing = sorted(faq_ids - set(assigned))
    unknown = sorted(set(assigned) - faq_ids)

    if duplicates:
        errors.append(f"FAQ asignadas a varias intenciones: {duplicates}.")
    if missing:
        errors.append(f"FAQ sin intencion principal: {missing}.")
    if unknown:
        errors.append(f"FAQ desconocidas en taxonomia: {unknown}.")
    if len({intent.id for intent in MAIN_INTENTS}) != len(MAIN_INTENTS):
        errors.append("Existen ids duplicados de intenciones principales.")
    return errors
