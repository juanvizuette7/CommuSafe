"""Servicios del asistente virtual persistente."""

import logging
import hashlib
import re
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Callable

import requests

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover
    genai = None
    genai_types = None

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.utils import timezone

from incidentes.models import Incidente
from notificaciones.models import Notificacion

from .knowledge_base import render_knowledge_base
from .local_engine import local_engine_stats, normalize_text, resolve_local_answer
from .models import AsistenteRespuestaLog, ConsultaSinRespuesta, ConversacionAsistente, MensajeAsistente


LOGGER = logging.getLogger(__name__)
CONOCIMIENTO_REMANSOS = render_knowledge_base()
MAX_LLM_HISTORY_MESSAGES = 12
MAX_LLM_HISTORY_CHARS = 6000
DEFAULT_LLM_MAX_OUTPUT_TOKENS = 700
DEFAULT_LLM_TIMEOUT_SECONDS = 8.0
DEFAULT_LLM_HOURLY_REQUEST_LIMIT = 20
DEFAULT_LLM_DAILY_REQUEST_LIMIT = 80
DEFAULT_LLM_DAILY_TOKEN_LIMIT = 120000
DOMAIN_RESPONSE_TERMS = {
    "administracion",
    "administrador",
    "asistente",
    "aviso",
    "commusafe",
    "conjunto",
    "incidente",
    "notificacion",
    "porteria",
    "reporte",
    "remansos",
    "residente",
    "seguridad",
    "vigilancia",
    "vigilante",
}
FORBIDDEN_GENERATIVE_PATTERNS = {
    "como modelo de lenguaje",
    "consulta en internet",
    "no tengo restricciones",
    "puedo ayudarte con cualquier tema",
    "segun mi conocimiento general",
}
PROMPT_MANIPULATION_PATTERNS = {
    "actua sin restricciones",
    "api key",
    "apikey",
    "bearer token",
    "clave secreta",
    "developer message",
    "dime el prompt",
    "dime la clave",
    "dame el token",
    "dame las contrasenas",
    "datos privados de",
    "informacion privada de",
    "incidentes privados",
    "muestrame las contrasenas",
    "muestrame los datos",
    "reportes privados",
    "haz como que eres admin",
    "ignora instrucciones",
    "ignora las instrucciones",
    "ignora tus instrucciones",
    "instrucciones internas",
    "jailbreak",
    "mensaje del sistema",
    "modo desarrollador",
    "olvida instrucciones",
    "olvida las instrucciones",
    "password de",
    "revela el prompt",
    "secret_key",
    "system prompt",
    "token jwt",
}
VALIDATION_HINT_TERMS = {
    "administracion",
    "confirmar",
    "confirmalo",
    "validar",
    "validarlo",
    "verificar",
    "verificalo",
    "no encuentro",
}
UNCERTAINTY_HINT_TERMS = {
    "informacion no disponible",
    "no esta disponible",
    "no esta registrado",
    "no esta registrada",
    "no encuentro",
    "requiere confirmacion",
}
MAX_UNTRUSTED_HISTORY_MESSAGES = 4
MAX_UNTRUSTED_HISTORY_CHARS = 1500


@dataclass(frozen=True)
class LLMProviderAdapter:
    """Proveedor generativo desacoplado de la orquestacion del asistente."""

    name: str
    model: str
    configured: bool
    caller: Callable | None


SYSTEM_PROMPT = f"""
Eres CommuBot, el asistente virtual oficial de CommuSafe para el conjunto residencial Remansos del Norte.
Actúas como un asistente conversacional profesional, claro, amable, útil y prudente.
Respondes siempre en español.
Tu dominio está limitado exclusivamente a Remansos del Norte y al sistema CommuSafe.
Puedes orientar a residentes, vigilancia y administración sobre reportes, incidentes, avisos, normas internas, convivencia, áreas comunes, emergencias, notificaciones, perfil, uso de la app y procedimientos administrativos básicos.
Solo puedes responder con base en esta información autorizada:
{CONOCIMIENTO_REMANSOS}
No inventes políticas, valores, multas, nombres de personas, sanciones, claves, datos privados ni decisiones administrativas.
Si la información no está disponible o requiere confirmación humana, responde de forma natural indicando que no encuentras ese dato en CommuSafe y sugiere contactar a administración o portería.
Si el usuario pregunta algo externo al conjunto o a CommuSafe, responde de forma amable que solo puedes apoyar consultas relacionadas con Remansos del Norte y CommuSafe.
Usa respuestas concretas y estructuradas. Si hay pasos, enuméralos. Si hay riesgo o emergencia, prioriza seguridad y contacto con portería o línea 123.
No uses Markdown decorativo, no uses negritas con asteriscos, no uses encabezados con numeral y no envuelvas palabras con símbolos. Responde en texto plano, con numeración simple cuando haya pasos.
Cuando el usuario pregunte cómo reportar un incidente, explica pasos concretos dentro de CommuSafe, como si el usuario ya estuviera usando la aplicación.
En preguntas sobre uso interno de la app, asume que el usuario ya inició sesión y está dentro de CommuSafe. No respondas con pasos genéricos como "descarga la app" o "inicia sesión" salvo que el usuario pregunte específicamente por acceso.
Usa expresiones como "según la información registrada en CommuSafe", "de acuerdo con la información disponible en el sistema" o "puedes realizar este proceso desde el módulo correspondiente" cuando ayuden a contextualizar la respuesta.
Mantén coherencia con el historial de la conversación y no contradigas mensajes anteriores salvo para corregir con claridad.
""".strip()


def crear_titulo_conversacion(mensaje):
    """Genera un título breve a partir del primer mensaje del usuario."""

    palabras = [palabra.strip(".,;:¿?¡!()[]{}") for palabra in mensaje.split()]
    palabras = [palabra for palabra in palabras if palabra]
    if not palabras:
        return "Nueva conversación"

    titulo = " ".join(palabras[:7]).strip()
    if len(palabras) > 7:
        titulo = f"{titulo}..."
    return titulo[:90]


def _valor_configurado(valor):
    valor_limpio = (valor or "").strip()
    if not valor_limpio:
        return False

    marcadores_invalidos = ["REEMPLAZAR", "PLACEHOLDER", "PEGA AQUI", "PEGA AQUÍ", "[", "]"]
    return not any(marcador in valor_limpio.upper() for marcador in marcadores_invalidos)


def _gemini_configurada():
    return genai is not None and _valor_configurado(getattr(settings, "GEMINI_API_KEY", ""))


def _anthropic_configurada():
    return Anthropic is not None and _valor_configurado(getattr(settings, "LLM_API_KEY", ""))


def _api_llm_configurada():
    return _gemini_configurada() or _anthropic_configurada()


def _llm_backup_enabled():
    return bool(getattr(settings, "LLM_BACKUP_ENABLED", True))


def _llm_max_output_tokens():
    return int(getattr(settings, "LLM_MAX_OUTPUT_TOKENS", DEFAULT_LLM_MAX_OUTPUT_TOKENS))


def _llm_timeout_seconds():
    return float(getattr(settings, "LLM_TIMEOUT_SECONDS", DEFAULT_LLM_TIMEOUT_SECONDS))


def _llm_hourly_request_limit():
    return int(getattr(settings, "LLM_HOURLY_REQUEST_LIMIT", DEFAULT_LLM_HOURLY_REQUEST_LIMIT))


def _llm_daily_request_limit():
    return int(getattr(settings, "LLM_DAILY_REQUEST_LIMIT", DEFAULT_LLM_DAILY_REQUEST_LIMIT))


def _llm_daily_token_limit():
    return int(getattr(settings, "LLM_DAILY_TOKEN_LIMIT", DEFAULT_LLM_DAILY_TOKEN_LIMIT))


def _normalizar_historial(historial):
    mensajes = []
    for item in historial:
        rol_original = item.get("rol") or item.get("role")
        rol = "assistant" if rol_original in {"assistant", "asistente", MensajeAsistente.Rol.ASISTENTE} else "user"
        contenido = (item.get("contenido") or item.get("mensaje") or item.get("content") or "").strip()
        if contenido:
            mensajes.append({"role": rol, "content": contenido})
    return mensajes


def _normalizar_seguridad(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return texto.encode("ascii", "ignore").decode("ascii").lower()


def _contiene_intento_manipulacion(texto):
    normalizado = _normalizar_seguridad(texto)
    return any(patron in normalizado for patron in PROMPT_MANIPULATION_PATTERNS)


def _redactar_sensibles(texto):
    texto = str(texto or "")
    patrones = [
        (r"AIza[0-9A-Za-z_\-]{20,}", "[API_KEY_REDACTADA]"),
        (r"(?i)\bbearer\s+[A-Za-z0-9._\-]+", "Bearer [TOKEN_REDACTADO]"),
        (r"(?i)\b(secret|token|api[_-]?key|password|clave)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTADO]"),
        (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "[EMAIL_REDACTADO]"),
        (r"\b3\d{9}\b", "[TELEFONO_REDACTADO]"),
    ]
    for patron, reemplazo in patrones:
        texto = re.sub(patron, reemplazo, texto)
    return texto[:4000]


def _preparar_historial_para_ia(historial, *, confiable=True):
    mensajes = _normalizar_historial(historial)
    if not confiable:
        mensajes = [mensaje for mensaje in mensajes if mensaje["role"] == "user"]
        mensajes = mensajes[-MAX_UNTRUSTED_HISTORY_MESSAGES:]

    seguros = []
    caracteres = 0
    for mensaje in mensajes:
        contenido = mensaje["content"].strip()
        if not contenido or _contiene_intento_manipulacion(contenido):
            continue
        if not confiable:
            disponible = MAX_UNTRUSTED_HISTORY_CHARS - caracteres
            if disponible <= 0:
                break
            contenido = contenido[:disponible]
            caracteres += len(contenido)
        seguros.append({"role": mensaje["role"], "content": contenido})
    return seguros


def _compactar_historial_para_ia(historial, *, confiable=True):
    """Reduce el historial enviado al LLM sin perder la memoria reciente."""

    mensajes = _preparar_historial_para_ia(historial, confiable=confiable)[-MAX_LLM_HISTORY_MESSAGES:]
    seleccionados = []
    caracteres = 0

    for item in reversed(mensajes):
        contenido = item["content"][:2000].strip()
        if not contenido:
            continue

        disponible = MAX_LLM_HISTORY_CHARS - caracteres
        if disponible <= 0:
            break
        if len(contenido) > disponible:
            contenido = contenido[-disponible:].strip()

        seleccionados.append({"role": item["role"], "content": contenido})
        caracteres += len(contenido)

    return list(reversed(seleccionados))


def _normalizar_historial_gemini(historial, mensaje_actual):
    lineas = []
    for item in historial:
        rol_original = item.get("rol") or item.get("role")
        rol = "Asistente" if rol_original in {"assistant", "asistente", MensajeAsistente.Rol.ASISTENTE} else "Usuario"
        contenido = (item.get("contenido") or item.get("mensaje") or item.get("content") or "").strip()
        if contenido:
            lineas.append(f"{rol}: {contenido}")
    lineas.append(f"Usuario: {mensaje_actual}")
    return "\n".join(lineas)


def _historial_desde_conversacion(conversacion):
    return [
        {
            "rol": mensaje.rol,
            "contenido": mensaje.contenido,
        }
        for mensaje in conversacion.mensajes.order_by("fecha_creacion")
    ]


def _contexto_usuario(usuario):
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return ""

    lineas = [f"Rol del usuario autenticado: {usuario.get_rol_display()}."]

    incidentes = Incidente.objects.select_related("reportado_por").order_by("-fecha_reporte")
    if usuario.es_residente:
        incidentes = incidentes.filter(reportado_por=usuario)
    incidentes = list(incidentes[:5])
    if incidentes:
        estados = Counter(incidente.get_estado_display() for incidente in incidentes)
        resumen_estados = ", ".join(f"{estado}: {cantidad}" for estado, cantidad in sorted(estados.items()))
        lineas.append(f"Incidentes recientes visibles: {len(incidentes)}. Resumen por estado: {resumen_estados}.")

    total_avisos = Notificacion.objects.filter(
        destinatario=usuario,
        tipo__in=[Notificacion.Tipo.AVISO_ADMIN, Notificacion.Tipo.EMERGENCIA],
    ).count()
    if total_avisos:
        lineas.append(f"Avisos administrativos o de emergencia disponibles: {total_avisos}.")

    return "\n".join(lineas)


def construir_system_prompt(usuario=None):
    contexto = _contexto_usuario(usuario)
    if not contexto:
        return SYSTEM_PROMPT
    return f"{SYSTEM_PROMPT}\n\nContexto operativo disponible para esta conversación:\n{contexto}"


def _respuesta_fallback(mensaje):
    texto = mensaje.lower()

    if any(palabra in texto for palabra in ["horario", "horarios", "salon", "salón", "zona comun", "zona común", "zonas comunes"]):
        return (
            "Según la información registrada en CommuSafe, las áreas comunes de Remansos del Norte funcionan de 6:00 a. m. a 10:00 p. m. "
            "La administración atiende de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sábados de 8:00 a. m. a 12:00 m."
        )
    if any(palabra in texto for palabra in ["emergencia", "gas", "incendio", "ambulancia", "urgencia"]):
        return (
            "Si se trata de una emergencia, contacta de inmediato a portería y, si hay riesgo para la vida o la seguridad, "
            "llama también a la línea 123. Si puedes hacerlo sin exponerte, registra el incidente en CommuSafe para dejar trazabilidad."
        )
    if any(palabra in texto for palabra in ["cuota", "administracion", "administración", "cartera", "pago"]):
        return (
            "De acuerdo con la información disponible en el sistema, las cuotas, recibos, paz y salvos y estados de cartera se validan con administración. "
            "No encuentro un valor exacto registrado en CommuSafe para esa consulta; verifica directamente con administración para recibir la información actualizada."
        )
    if any(palabra in texto for palabra in ["visitante", "visitantes", "domiciliario", "domiciliarios", "proveedor", "proveedores", "ingreso"]):
        return (
            "Para gestionar visitantes, domiciliarios o proveedores, informa a portería los datos básicos: nombre, unidad a la que se dirige, motivo de visita, hora aproximada y placa si ingresa con vehículo. "
            "Vigilancia puede solicitar confirmación cuando el visitante no esté anunciado o haya una novedad de seguridad."
        )
    if any(palabra in texto for palabra in ["parqueadero", "parqueaderos", "vehiculo", "vehículo", "placa", "carro", "moto"]):
        return (
            "Si hay una novedad en parqueaderos, registra un incidente con ubicación exacta, descripción, placa visible si aplica y evidencia fotográfica si es seguro tomarla. "
            "Si un vehículo bloquea el paso, avisa también a portería para gestionar apoyo inmediato."
        )
    if any(palabra in texto for palabra in ["mascota", "mascotas", "perro", "gato", "excremento"]):
        return (
            "Según la información registrada en CommuSafe, las mascotas deben transitar con control o correa en zonas comunes y sus propietarios deben recoger los residuos. "
            "Si hay ruido, agresividad, suciedad o una mascota extraviada, crea un reporte de convivencia respetuoso indicando lugar, hora, frecuencia y evidencia si la tienes."
        )
    if any(palabra in texto for palabra in ["norma", "convivencia", "ruido", "mascota", "reglamento"]):
        return (
            "Las normas básicas de convivencia incluyen respetar el horario de descanso entre 10:00 p. m. y 6:00 a. m., "
            "mantener comunicación respetuosa, usar adecuadamente las zonas comunes, controlar el ruido y reportar conflictos recurrentes desde CommuSafe."
        )
    if any(palabra in texto for palabra in ["daño", "dano", "mantenimiento", "luz", "iluminacion", "iluminación", "cerradura", "citofono", "citófono", "puerta", "pasillo", "limpieza"]):
        return (
            "Para reportar mantenimiento o daños comunes, usa Incidentes > Nuevo y selecciona Infraestructura. "
            "Incluye qué elemento falla, ubicación exacta, desde cuándo ocurre, si afecta seguridad o movilidad y hasta 3 fotos si las tienes."
        )
    if any(
        frase in texto
        for frase in [
            "como reporto",
            "cómo reporto",
            "como puedo reportar",
            "cómo puedo reportar",
            "reportar un incidente",
            "crear incidente",
            "nuevo incidente",
            "hacer un reporte",
        ]
    ):
        return (
            "Para reportar un incidente en CommuSafe:\n"
            "1. Entra a la pestaña Incidentes.\n"
            "2. Toca el botón Nuevo.\n"
            "3. Escribe un título corto y selecciona la categoría: Seguridad, Convivencia, Infraestructura o Emergencia.\n"
            "4. Describe qué pasó, dónde ocurrió y agrega la ubicación de referencia.\n"
            "5. Si tienes evidencia, adjunta hasta 3 fotos desde cámara o galería.\n"
            "6. Toca Reportar incidente. Después puedes abrir el detalle para ver el estado, historial y respuestas de vigilancia."
        )
    if any(palabra in texto for palabra in ["estado", "seguimiento", "historial", "avance"]):
        return (
            "Para revisar el avance de un incidente, entra a Incidentes y toca el reporte que quieres consultar. "
            "En el detalle verás el estado actual, la descripción, evidencias y el historial de cambios con comentarios."
        )
    if any(palabra in texto for palabra in ["aviso", "alerta", "notificacion", "notificación"]):
        return (
            "Los avisos y alertas aparecen en la sección Alertas de CommuSafe. Allí puedes revisar comunicados de administración, "
            "cambios de estado de incidentes y emergencias enviadas al conjunto. Algunos avisos pueden ser informativos y otros pueden requerir una acción concreta."
        )
    if any(palabra in texto for palabra in ["contraseña", "contrasena", "clave", "no puedo ingresar", "login", "sesion", "sesión"]):
        return (
            "Para ingresar a CommuSafe usa el correo registrado y la contraseña asignada. "
            "Si no puedes acceder o necesitas restablecer la contraseña, solicita apoyo a administración para validar tu cuenta y actualizar el acceso."
        )
    if any(palabra in texto for palabra in ["app", "commusafe", "incidente", "reporte"]):
        return (
            "En CommuSafe puedes reportar incidentes, consultar el estado de tus casos, revisar notificaciones, recibir avisos y usar este asistente. "
            "Si quieres reportar, usa Incidentes > Nuevo y completa el formulario con categoría, descripción, ubicación y evidencias."
        )

    return (
        "Solo puedo apoyar consultas relacionadas con Remansos del Norte y el sistema CommuSafe. "
        "No encuentro un dato exacto registrado en CommuSafe para esa consulta; te recomiendo verificarlo directamente con administración."
    )


def _extraer_texto_anthropic(respuesta):
    bloques = getattr(respuesta, "content", []) or []
    textos = [getattr(bloque, "text", "").strip() for bloque in bloques if getattr(bloque, "text", "").strip()]
    return "\n".join(textos).strip()


def _limpiar_respuesta_ia(texto):
    """Convierte markdown decorativo del LLM en texto plano para la app móvil."""

    texto = (texto or "").strip()
    if not texto:
        return ""

    texto = re.sub(r"[*_]{2,}", "", texto)
    texto = re.sub(r"^\s{0,3}#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*[\*\u2022]\s+", "- ", texto, flags=re.MULTILINE)
    texto = re.sub(r"`{1,3}", "", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _llamar_anthropic(mensaje, historial, system_prompt):
    mensajes = _normalizar_historial(historial)
    mensajes.append({"role": "user", "content": mensaje})

    cliente = Anthropic(api_key=settings.LLM_API_KEY)
    respuesta = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=_llm_max_output_tokens(),
        system=system_prompt,
        messages=mensajes,
    )
    return _extraer_texto_anthropic(respuesta)


def _llamar_gemini(mensaje, historial, system_prompt):
    cliente = genai.Client(api_key=settings.GEMINI_API_KEY)
    contenido = _normalizar_historial_gemini(historial, mensaje)
    respuesta = cliente.models.generate_content(
        model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=contenido,
        config=genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=_llm_max_output_tokens(),
            temperature=0.25,
        ),
    )
    return (getattr(respuesta, "text", "") or "").strip()


def _llm_provider_registry():
    return [
        LLMProviderAdapter(
            name="gemini",
            model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite"),
            configured=_gemini_configurada(),
            caller=_llamar_gemini if _gemini_configurada() else None,
        ),
        LLMProviderAdapter(
            name="anthropic",
            model="claude-haiku-4-5-20251001",
            configured=_anthropic_configurada(),
            caller=_llamar_anthropic if _anthropic_configurada() else None,
        ),
    ]


def _resolver_adaptador_proveedor():
    proveedor_preferido = (getattr(settings, "LLM_PROVIDER", "gemini") or "gemini").lower().strip()
    providers = _llm_provider_registry()

    for provider in providers:
        if provider.name == proveedor_preferido and provider.configured:
            return provider
    for provider in providers:
        if provider.configured:
            return provider
    return LLMProviderAdapter("fallback", "", False, None)


def _resolver_proveedor():
    """Contrato historico: devuelve nombre y callable del proveedor activo."""

    provider = _resolver_adaptador_proveedor()
    return provider.name, provider.caller


def _modelo_por_proveedor(proveedor):
    if proveedor == "gemini":
        return getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite")
    if proveedor == "anthropic":
        return "claude-haiku-4-5-20251001"
    return ""


def _decimal_confianza(valor):
    try:
        return Decimal(str(round(float(valor or 0), 4)))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _tokens_ia_en_rango(fecha_inicio, proveedor=None):
    queryset = AsistenteRespuestaLog.objects.filter(
        modo=AsistenteRespuestaLog.Modo.IA,
        fecha_creacion__gte=fecha_inicio,
    )
    if proveedor:
        queryset = queryset.filter(proveedor=proveedor)
    aggregate = queryset.aggregate(
        total_entrada=Sum("tokens_entrada"),
        total_salida=Sum("tokens_salida"),
        total=Count("id"),
    )
    return {
        "consultas": aggregate["total"] or 0,
        "tokens": (aggregate["total_entrada"] or 0) + (aggregate["total_salida"] or 0),
    }


def _estado_cuota_llm(proveedor):
    """Valida limites antes de usar IA externa para evitar gasto no controlado."""

    now = timezone.now()
    try:
        uso_hora = _tokens_ia_en_rango(now - timedelta(hours=1), proveedor)
        uso_dia = _tokens_ia_en_rango(now - timedelta(days=1), proveedor)
    except Exception as exc:
        LOGGER.warning("llm_quota_unavailable", extra={"provider": proveedor, "error": str(exc)})
        return {
            "permitido": False,
            "motivo": "cuota_no_verificable",
            "proveedor": proveedor,
        }

    hourly_limit = _llm_hourly_request_limit()
    daily_limit = _llm_daily_request_limit()
    daily_token_limit = _llm_daily_token_limit()
    allowed = (
        uso_hora["consultas"] < hourly_limit
        and uso_dia["consultas"] < daily_limit
        and uso_dia["tokens"] < daily_token_limit
    )
    reason = ""
    if uso_hora["consultas"] >= hourly_limit:
        reason = "limite_horario_alcanzado"
    elif uso_dia["consultas"] >= daily_limit:
        reason = "limite_diario_alcanzado"
    elif uso_dia["tokens"] >= daily_token_limit:
        reason = "limite_diario_tokens_alcanzado"

    return {
        "permitido": allowed,
        "motivo": reason,
        "proveedor": proveedor,
        "uso_hora": uso_hora,
        "uso_dia": uso_dia,
        "limites": {
            "consultas_hora": hourly_limit,
            "consultas_dia": daily_limit,
            "tokens_dia": daily_token_limit,
        },
    }


def _estimar_tokens_entrada_ia(mensaje, historial_llm, system_prompt):
    return (
        _estimar_tokens(system_prompt)
        + _estimar_tokens(mensaje)
        + sum(_estimar_tokens(item["content"]) for item in historial_llm)
    )


def _agregar_metricas_ahorro(resultado, *, mensaje, usuario=None, historial=None, historial_confiable=True):
    """Registra ahorro estimado cuando la respuesta evita llamar a Gemini/LLM."""

    historial_llm = _compactar_historial_para_ia(historial or [], confiable=historial_confiable)
    tokens_ahorrados = _estimar_tokens_entrada_ia(mensaje, historial_llm, construir_system_prompt(usuario))
    metadata = resultado.setdefault("metadata", {})
    metadata["tokens_ahorrados_estimados"] = tokens_ahorrados
    metadata["gemini_evitado"] = True
    metadata["politica_ia"] = "local_first"
    resultado["tokens_ahorrados_estimados"] = tokens_ahorrados
    return resultado


def metricas_uso_asistente(horas=24):
    """Mide uso local, aclaraciones, IA y ahorro estimado con base en logs."""

    since = timezone.now() - timedelta(hours=int(horas or 24))
    logs = list(
        AsistenteRespuestaLog.objects.filter(fecha_creacion__gte=since).values(
            "modo",
            "proveedor",
            "tokens_entrada",
            "tokens_salida",
            "metadata",
        )
    )
    total = len(logs)
    sin_gemini = 0
    aclaraciones = 0
    uso_ia = 0
    uso_gemini = 0
    tokens_ia = 0
    tokens_ahorrados = 0

    for log in logs:
        modo = log["modo"]
        proveedor = log["proveedor"]
        metadata = log["metadata"] or {}
        if proveedor != "gemini":
            sin_gemini += 1
        if modo == AsistenteRespuestaLog.Modo.ACLARACION:
            aclaraciones += 1
        if modo == AsistenteRespuestaLog.Modo.IA:
            uso_ia += 1
            tokens_ia += (log["tokens_entrada"] or 0) + (log["tokens_salida"] or 0)
        if proveedor == "gemini":
            uso_gemini += 1
        tokens_ahorrados += int(metadata.get("tokens_ahorrados_estimados", 0) or 0)

    return {
        "ventana_horas": int(horas or 24),
        "consultas_totales": total,
        "resueltas_sin_gemini": sin_gemini,
        "requieren_aclaracion": aclaraciones,
        "usan_ia_externa": uso_ia,
        "usan_gemini": uso_gemini,
        "tokens_ia_estimados": tokens_ia,
        "tokens_ahorrados_estimados": tokens_ahorrados,
        "porcentaje_sin_gemini": round((sin_gemini / total) * 100, 2) if total else 0,
    }


def _nlp_service_configurado():
    return bool(getattr(settings, "COMMUSAFE_NLP_SERVICE_URL", "").strip())


def _resolver_con_servicio_nlp(mensaje, rol):
    """Usa el servicio Flask auxiliar si esta configurado; Django conserva fallback interno."""

    service_url = getattr(settings, "COMMUSAFE_NLP_SERVICE_URL", "").strip().rstrip("/")
    if not service_url:
        return None

    headers = {"Content-Type": "application/json"}
    service_key = getattr(settings, "COMMUSAFE_NLP_SERVICE_KEY", "").strip()
    if service_key:
        headers["X-CommuSafe-NLP-Key"] = service_key

    try:
        response = requests.post(
            f"{service_url}/v1/infer",
            json={"mensaje": mensaje, "rol": rol},
            headers=headers,
            timeout=float(getattr(settings, "COMMUSAFE_NLP_SERVICE_TIMEOUT", 2.5)),
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("resultado")
        if isinstance(result, dict) and result.get("action"):
            result.setdefault("service_bridge", "flask")
            return result
    except (requests.RequestException, ValueError, TypeError) as exc:
        LOGGER.warning("nlp_service_unavailable", extra={"error": str(exc)})
    return None


def _estimar_tokens(texto):
    if not texto:
        return 0
    return max(1, int(len(str(texto).split()) * 1.35))


def _normalizar_para_validacion(texto):
    texto = texto or ""
    texto = texto.lower()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    return texto


def _validar_respuesta_generativa(texto):
    """Bloquea respuestas externas si parecen fuera de dominio o no verificables."""

    normalizado = _normalizar_para_validacion(texto)
    if len(normalizado.split()) < 5:
        return False, "respuesta_demasiado_corta"
    if any(pattern in normalizado for pattern in FORBIDDEN_GENERATIVE_PATTERNS):
        return False, "patron_generativo_no_permitido"
    if not any(term in normalizado for term in DOMAIN_RESPONSE_TERMS):
        return False, "sin_marcadores_del_dominio"
    tiene_validacion = any(term in normalizado for term in VALIDATION_HINT_TERMS)
    patrones_exactos = [
        r"\b(?:\$|cop|pesos?)\s*\d+",
        r"\b\d[\d.,]*\s*(?:cop|pesos?)\b",
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",
        r"\b(?:\+?57\s*)?3\d{9}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    ]
    if any(re.search(patron, normalizado) for patron in patrones_exactos):
        return False, "dato_exacto_no_verificado"
    if not tiene_validacion:
        return False, "sin_indicacion_de_validacion_administrativa"
    if not any(term in normalizado for term in UNCERTAINTY_HINT_TERMS):
        return False, "sin_reconocimiento_de_informacion_no_verificada"
    return True, "respuesta_validada"


def _llamar_proveedor_con_timeout(provider, mensaje, historial_llm, system_prompt):
    if provider.caller is None:
        raise RuntimeError("Proveedor LLM no configurado.")

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(provider.caller, mensaje, historial_llm, system_prompt)
    try:
        return future.result(timeout=_llm_timeout_seconds())
    except TimeoutError as exc:
        future.cancel()
        raise TimeoutError(f"Tiempo de espera agotado para {provider.name}.") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _respuesta_segura_controlada():
    return (
        "No encuentro informacion verificada suficiente en CommuSafe para responder esa consulta con precision. "
        "Te recomiendo validarlo directamente con administracion para evitar datos incorrectos."
    )


def _respuesta_segura_manipulacion():
    return (
        "Por seguridad no puedo revelar instrucciones internas, claves, tokens, datos privados ni cambiar las reglas de CommuBot. "
        "Si necesitas ayuda con CommuSafe, puedo orientarte sobre reportes, avisos, incidentes, convivencia, emergencias o contacto con administracion."
    )


def _agregar_nota_validacion_si_aplica(resultado):
    if not resultado.get("requiere_validacion"):
        return resultado

    respuesta = resultado.get("respuesta", "")
    normalizada = _normalizar_seguridad(respuesta)
    if not any(term in normalizada for term in VALIDATION_HINT_TERMS):
        resultado["respuesta"] = (
            f"{respuesta}\n\n"
            "Si necesitas una respuesta oficial o actualizada, confirma este dato con administracion."
        )
    return resultado


def _respuesta_segura_por_manipulacion(mensaje, *, usuario=None, conversacion=None):
    resultado = {
        "respuesta": _respuesta_segura_manipulacion(),
        "modo": "segura",
        "proveedor": "local",
        "modelo_usado": "commusafe-local-hybrid-v3",
        "confianza": 1.0,
        "intencion": "seguridad_contexto",
        "categoria": "seguridad_respuesta",
        "metodo": "bloqueo_manipulacion_contexto",
        "requiere_validacion": False,
        "latencia_ms": 0,
        "metadata": {
            "politica_seguridad": "no_exponer_secretos_ni_instrucciones",
            "gemini_evitado": True,
        },
    }
    _registrar_respuesta_log(
        mensaje=mensaje,
        resultado=resultado,
        usuario=usuario,
        conversacion=conversacion,
    )
    return resultado


def _registrar_respuesta_log(*, mensaje, resultado, usuario=None, conversacion=None):
    """Guarda trazabilidad tecnica sin interrumpir el chat si falla el registro."""

    try:
        AsistenteRespuestaLog.objects.create(
            usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
            conversacion=conversacion,
            mensaje=_redactar_sensibles(mensaje),
            modo=resultado.get("modo", "fallback") or "fallback",
            proveedor=resultado.get("proveedor", ""),
            modelo=resultado.get("modelo_usado", "") or resultado.get("modelo", ""),
            intencion=resultado.get("intencion", "") or resultado.get("intent", ""),
            categoria=resultado.get("categoria", ""),
            metodo=resultado.get("metodo", "") or resultado.get("method", ""),
            confianza=_decimal_confianza(resultado.get("confianza", 0)),
            latencia_ms=int(resultado.get("latencia_ms", 0) or 0),
            tokens_entrada=resultado.get("tokens_entrada"),
            tokens_salida=resultado.get("tokens_salida"),
            requiere_validacion=bool(resultado.get("requiere_validacion", False)),
            metadata=resultado.get("metadata", {}),
        )
    except Exception:
        pass


def _payload_desde_local(local_result):
    return {
        "respuesta": local_result["respuesta"],
        "modo": local_result["mode"],
        "proveedor": local_result["provider"],
        "modelo_usado": local_result.get("model", ""),
        "confianza": local_result.get("confidence", 0),
        "intencion": local_result.get("intent", ""),
        "categoria": local_result.get("category", ""),
        "metodo": local_result.get("method", ""),
        "requiere_validacion": local_result.get("requires_validation", False),
        "latencia_ms": local_result.get("latency_ms", 0),
        "metadata": {
            "entry_id": local_result.get("entry_id", ""),
            "subintent": local_result.get("subintent", ""),
            "verified": local_result.get("verified", False),
            "verification_status": local_result.get("verification_status", ""),
            "validity_status": local_result.get("validity_status", ""),
            "valid_from": local_result.get("valid_from", ""),
            "valid_until": local_result.get("valid_until", ""),
            "options": local_result.get("options", []),
            "score_parts": local_result.get("score_parts", {}),
            "updated_at": local_result.get("updated_at", ""),
        },
    }


def _registrar_consulta_sin_respuesta(mensaje, rol, local_result):
    """Agrupa vacios reales de conocimiento sin guardar datos sensibles."""

    accion = local_result.get("action")
    metodo = local_result.get("method", "")
    if accion != "fallback_allowed" and not (accion == "safe" and metodo == "sin_candidatos"):
        return

    consulta_normalizada = normalize_text(mensaje)
    if not consulta_normalizada:
        return

    huella = hashlib.sha256(consulta_normalizada.encode("utf-8")).hexdigest()
    confianza = local_result.get("confidence")
    try:
        confianza = Decimal(str(confianza)) if confianza is not None else None
    except (InvalidOperation, TypeError, ValueError):
        confianza = None

    for intento in range(2):
        try:
            with transaction.atomic():
                consulta, creada = ConsultaSinRespuesta.objects.select_for_update().get_or_create(
                    huella=huella,
                    rol=(rol or "RESIDENTE").upper(),
                    defaults={
                        "consulta_muestra": _redactar_sensibles(mensaje),
                        "consulta_normalizada": consulta_normalizada,
                        "confianza_maxima": confianza,
                        "intencion_sugerida": local_result.get("intent", ""),
                    },
                )
                if creada:
                    return

                consulta.cantidad += 1
                if confianza is not None and (
                    consulta.confianza_maxima is None or confianza > consulta.confianza_maxima
                ):
                    consulta.confianza_maxima = confianza
                if not consulta.intencion_sugerida:
                    consulta.intencion_sugerida = local_result.get("intent", "")
                consulta.save(
                    update_fields=[
                        "cantidad",
                        "confianza_maxima",
                        "intencion_sugerida",
                        "fecha_ultima_consulta",
                    ]
                )
                return
        except IntegrityError:
            if intento == 0:
                continue
            LOGGER.exception("Colision persistente al registrar una consulta sin respuesta.")
        except Exception:
            LOGGER.exception("No fue posible registrar una consulta sin respuesta.")
            return


def generar_respuesta_asistente(mensaje, historial=None, usuario=None, conversacion=None, historial_confiable=True):
    """Genera respuesta hibrida: local verificado primero, IA solo como respaldo."""

    inicio = time.perf_counter()
    mensaje = str(mensaje or "").strip()
    historial = historial or []
    rol = getattr(usuario, "rol", "RESIDENTE") if usuario else "RESIDENTE"

    if _contiene_intento_manipulacion(mensaje):
        return _respuesta_segura_por_manipulacion(
            mensaje,
            usuario=usuario,
            conversacion=conversacion,
        )

    resultado_interno = resolve_local_answer(mensaje, rol)
    _registrar_consulta_sin_respuesta(mensaje, rol, resultado_interno)
    resultado_auxiliar = _resolver_con_servicio_nlp(mensaje, rol)
    local_result = resultado_interno
    if (
        resultado_auxiliar
        and resultado_interno.get("action") in {"fallback_allowed", "safe"}
        and resultado_auxiliar.get("action") in {"answer", "clarify"}
    ):
        local_result = resultado_auxiliar

    if local_result["action"] in {"answer", "clarify", "safe"}:
        resultado = _payload_desde_local(local_result)
        resultado = _agregar_nota_validacion_si_aplica(resultado)
        resultado = _agregar_metricas_ahorro(
            resultado,
            mensaje=mensaje,
            usuario=usuario,
            historial=historial,
            historial_confiable=historial_confiable,
        )
        _registrar_respuesta_log(
            mensaje=mensaje,
            resultado=resultado,
            usuario=usuario,
            conversacion=conversacion,
        )
        return resultado

    provider = _resolver_adaptador_proveedor()
    proveedor = provider.name
    system_prompt = construir_system_prompt(usuario)
    quota_status = _estado_cuota_llm(proveedor) if provider.configured else {"permitido": False, "motivo": "sin_proveedor_configurado"}

    if _llm_backup_enabled() and provider.caller is not None and quota_status.get("permitido"):
        try:
            historial_llm = _compactar_historial_para_ia(historial, confiable=historial_confiable)
            tokens_entrada = _estimar_tokens_entrada_ia(mensaje, historial_llm, system_prompt)
            texto = _limpiar_respuesta_ia(
                _llamar_proveedor_con_timeout(provider, mensaje, historial_llm, system_prompt)
            )
            respuesta_valida, motivo_validacion = _validar_respuesta_generativa(texto)
            if texto:
                latencia_ms = int((time.perf_counter() - inicio) * 1000)
                if respuesta_valida:
                    resultado = {
                        "respuesta": texto,
                        "modo": "ia",
                        "proveedor": proveedor,
                        "modelo_usado": provider.model,
                        "confianza": local_result.get("confidence", 0),
                        "intencion": local_result.get("intent", "respaldo_generativo"),
                        "categoria": local_result.get("category", "respaldo_generativo"),
                        "metodo": "ia_respaldo_controlado_con_contexto_verificado",
                        "requiere_validacion": True,
                        "latencia_ms": latencia_ms,
                        "tokens_entrada": tokens_entrada,
                        "tokens_salida": _estimar_tokens(texto),
                        "metadata": {
                            "local_confidence": local_result.get("confidence", 0),
                            "local_method": local_result.get("method", ""),
                            "historial_mensajes_enviados": len(historial_llm),
                            "historial_caracteres_enviados": sum(len(item["content"]) for item in historial_llm),
                            "tokens_estimados": True,
                            "politica_ia": "respaldo_controlado",
                            "cuota": quota_status,
                            "validacion_respuesta": motivo_validacion,
                            "timeout_segundos": _llm_timeout_seconds(),
                        },
                    }
                    resultado = _agregar_nota_validacion_si_aplica(resultado)
                    _registrar_respuesta_log(
                        mensaje=mensaje,
                        resultado=resultado,
                        usuario=usuario,
                        conversacion=conversacion,
                    )
                    return resultado
                local_result["llm_error"] = motivo_validacion
            else:
                local_result["llm_error"] = "respuesta_vacia_del_proveedor"
        except Exception as exc:
            local_result["llm_error"] = str(exc)

    resultado = {
        "respuesta": _respuesta_segura_controlada(),
        "modo": "segura",
        "proveedor": "local",
        "modelo_usado": "commusafe-local-hybrid-v3",
        "confianza": local_result.get("confidence", 0),
        "intencion": local_result.get("intent", "sin_intencion_confiable"),
        "categoria": local_result.get("category", "seguridad_respuesta"),
        "metodo": "respuesta_segura_sin_ia_disponible",
        "requiere_validacion": True,
        "latencia_ms": int((time.perf_counter() - inicio) * 1000),
        "metadata": {
            "local_result": {
                "action": local_result.get("action"),
                "method": local_result.get("method"),
                "entry_id": local_result.get("entry_id"),
                "subintent": local_result.get("subintent", ""),
            },
            "llm_disponible": bool(provider.caller),
            "llm_backup_enabled": _llm_backup_enabled(),
            "llm_error": local_result.get("llm_error", ""),
            "cuota": quota_status,
        },
    }
    resultado = _agregar_metricas_ahorro(
        resultado,
        mensaje=mensaje,
        usuario=usuario,
        historial=historial,
        historial_confiable=historial_confiable,
    )
    _registrar_respuesta_log(
        mensaje=mensaje,
        resultado=resultado,
        usuario=usuario,
        conversacion=conversacion,
    )
    return resultado


@transaction.atomic
def procesar_mensaje_conversacion(*, conversacion, mensaje, usuario):
    """Persiste el mensaje del usuario, genera respuesta y guarda la respuesta."""

    conversacion = ConversacionAsistente.objects.select_for_update().get(
        pk=conversacion.pk,
        usuario=usuario,
    )
    mensaje = mensaje.strip()
    historial = _historial_desde_conversacion(conversacion)
    if conversacion.titulo.lower().startswith("nueva conversaci"):
        conversacion.titulo = crear_titulo_conversacion(mensaje)
        conversacion.save(update_fields=["titulo", "fecha_actualizacion"])

    mensaje_usuario = MensajeAsistente.objects.create(
        conversacion=conversacion,
        rol=MensajeAsistente.Rol.USUARIO,
        contenido=mensaje,
    )
    resultado = generar_respuesta_asistente(
        mensaje,
        historial,
        usuario=usuario,
        conversacion=conversacion,
    )
    mensaje_asistente = MensajeAsistente.objects.create(
        conversacion=conversacion,
        rol=MensajeAsistente.Rol.ASISTENTE,
        contenido=resultado["respuesta"],
    )
    conversacion.fecha_actualizacion = timezone.now()
    conversacion.save(update_fields=["fecha_actualizacion"])

    return {
        "conversacion": conversacion,
        "mensaje_usuario": mensaje_usuario,
        "mensaje_asistente": mensaje_asistente,
        **resultado,
    }
