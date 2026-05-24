"""Servicios del asistente virtual persistente."""

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
from django.db import transaction
from django.utils import timezone

from incidentes.models import Incidente
from notificaciones.models import Notificacion

from .models import ConversacionAsistente, MensajeAsistente


CONOCIMIENTO_REMANSOS = """
Conjunto residencial: Remansos del Norte.
Administración: atención de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sábados de 8:00 a. m. a 12:00 m.
Portería y vigilancia: atención permanente 24/7.
Horarios de áreas comunes: de 6:00 a. m. a 10:00 p. m.
Normas de convivencia base: respetar horarios de descanso entre 10:00 p. m. y 6:00 a. m., recoger excrementos de mascotas, usar correa en zonas comunes, no obstruir pasillos ni escaleras, respetar el reglamento de uso de zonas comunes.
Procedimiento de incidentes en CommuSafe: el residente reporta, vigilancia atiende, administración supervisa y puede cerrar el caso.
Emergencias: contactar portería de inmediato y, si la situación es crítica, llamar a la línea 123.
Cuotas de administración: se consultan y gestionan con administración; si el usuario requiere valores exactos o estado de cartera, debe contactar directamente a la administración.
Uso de CommuSafe: permite iniciar sesión, reportar incidentes, ver notificaciones, consultar estados, recibir avisos y conversar con el asistente.
Reporte de incidentes en la app móvil: el usuario ya está dentro de CommuSafe. Para reportar debe ir a la pestaña Incidentes, tocar el botón Nuevo, escribir un título claro, elegir categoría, describir lo ocurrido, agregar ubicación de referencia, adjuntar hasta 3 fotos si las tiene y tocar Reportar incidente. Luego puede abrir el detalle para revisar estado, historial y notificaciones.
Avisos: administración y vigilancia pueden enviar avisos informativos o alertas a residentes o usuarios seleccionados. Administración también puede programar avisos recurrentes por días.
El asistente puede explicar procedimientos, orientar sobre convivencia, uso de la plataforma, reportes, avisos, notificaciones, emergencias y preguntas frecuentes del conjunto.
Si una pregunta sale de este alcance, el asistente debe decirlo claramente y sugerir contactar a administración.
""".strip()


SYSTEM_PROMPT = f"""
Eres CommuBot, el asistente virtual oficial de CommuSafe para el conjunto residencial Remansos del Norte.
Actúas como un asistente conversacional profesional, claro, amable, útil y prudente.
Respondes siempre en español.
Tu dominio está limitado exclusivamente a Remansos del Norte y al sistema CommuSafe.
Puedes orientar a residentes, vigilancia y administración sobre reportes, incidentes, avisos, normas internas, convivencia, áreas comunes, emergencias, notificaciones, perfil, uso de la app y procedimientos administrativos básicos.
Solo puedes responder con base en esta información autorizada:
{CONOCIMIENTO_REMANSOS}
No inventes políticas, valores, multas, nombres de personas, sanciones, claves, datos privados ni decisiones administrativas.
Si la información no está disponible o requiere confirmación humana, dilo con claridad y sugiere contactar a administración o portería.
Si el usuario pregunta algo externo al conjunto o a CommuSafe, responde de forma amable que solo puedes apoyar consultas relacionadas con Remansos del Norte y CommuSafe.
Usa respuestas concretas y estructuradas. Si hay pasos, enuméralos. Si hay riesgo o emergencia, prioriza seguridad y contacto con portería/línea 123.
Cuando el usuario pregunte cómo reportar un incidente, explica pasos concretos dentro de CommuSafe, como si el usuario ya estuviera usando la aplicación.
En preguntas sobre uso interno de la app, asume que el usuario ya inició sesión y está dentro de CommuSafe. No respondas con pasos genéricos como "descarga la app" o "inicia sesión" salvo que el usuario pregunte específicamente por acceso.
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


def _normalizar_historial(historial):
    mensajes = []
    for item in historial:
        rol_original = item.get("rol") or item.get("role")
        rol = "assistant" if rol_original in {"assistant", "asistente", MensajeAsistente.Rol.ASISTENTE} else "user"
        contenido = (item.get("contenido") or item.get("mensaje") or item.get("content") or "").strip()
        if contenido:
            mensajes.append({"role": rol, "content": contenido})
    return mensajes


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

    lineas = [
        f"Usuario autenticado: {usuario.nombre_completo}.",
        f"Rol del usuario: {usuario.get_rol_display()}.",
    ]
    if usuario.es_residente and usuario.unidad_residencial:
        lineas.append(f"Unidad residencial: {usuario.unidad_residencial}.")
    elif usuario.es_vigilante:
        lineas.append(f"Referencia operativa: {usuario.unidad_residencial or 'Portería'}.")
    elif usuario.es_administrador:
        lineas.append("Referencia operativa: Administración.")

    incidentes = Incidente.objects.select_related("reportado_por").order_by("-fecha_reporte")
    if usuario.es_residente:
        incidentes = incidentes.filter(reportado_por=usuario)
    incidentes = incidentes[:5]
    if incidentes:
        lineas.append("Incidentes recientes visibles para el usuario:")
        for incidente in incidentes:
            lineas.append(
                "- "
                f"{incidente.titulo} | {incidente.get_categoria_display()} | "
                f"{incidente.get_prioridad_display()} | {incidente.get_estado_display()} | "
                f"{incidente.ubicacion_referencia or 'sin ubicación'}"
            )

    avisos = Notificacion.objects.filter(
        destinatario=usuario,
        tipo__in=[Notificacion.Tipo.AVISO_ADMIN, Notificacion.Tipo.EMERGENCIA],
    ).order_by("-fecha_envio")[:5]
    if avisos:
        lineas.append("Avisos recientes del usuario:")
        for aviso in avisos:
            lineas.append(f"- {aviso.titulo}: {aviso.cuerpo[:140]}")

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
            "En Remansos del Norte, las áreas comunes funcionan de 6:00 a. m. a 10:00 p. m. "
            "La administración atiende de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sábados de 8:00 a. m. a 12:00 m."
        )
    if any(palabra in texto for palabra in ["emergencia", "gas", "incendio", "ambulancia", "urgencia"]):
        return (
            "Si se trata de una emergencia, contacta de inmediato a portería y, si hay riesgo para la vida o la seguridad, "
            "llama también a la línea 123. Si puedes hacerlo sin exponerte, registra el incidente en CommuSafe para dejar trazabilidad."
        )
    if any(palabra in texto for palabra in ["cuota", "administracion", "administración", "cartera", "pago"]):
        return (
            "Las cuotas de administración y el estado de cartera se gestionan directamente con la administración del conjunto. "
            "Si necesitas el valor exacto o confirmar un pago, debes comunicarte con administración."
        )
    if any(palabra in texto for palabra in ["norma", "convivencia", "ruido", "mascota", "reglamento"]):
        return (
            "Las normas básicas de convivencia incluyen respetar el horario de descanso entre 10:00 p. m. y 6:00 a. m., "
            "usar correa para las mascotas en zonas comunes, recoger sus residuos y no obstruir pasillos o escaleras."
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
            "cambios de estado de incidentes y emergencias enviadas al conjunto."
        )
    if any(palabra in texto for palabra in ["app", "commusafe", "incidente", "reporte"]):
        return (
            "En CommuSafe puedes reportar incidentes, consultar el estado de tus casos, revisar notificaciones, recibir avisos y usar este asistente. "
            "Si quieres reportar, usa Incidentes > Nuevo y completa el formulario con categoría, descripción, ubicación y evidencias."
        )

    return (
        "Solo puedo apoyar consultas relacionadas con Remansos del Norte y el sistema CommuSafe. "
        "Para información no disponible en el sistema, contacta directamente a administración."
    )


def _extraer_texto_anthropic(respuesta):
    bloques = getattr(respuesta, "content", []) or []
    textos = [getattr(bloque, "text", "").strip() for bloque in bloques if getattr(bloque, "text", "").strip()]
    return "\n".join(textos).strip()


def _llamar_anthropic(mensaje, historial, system_prompt):
    mensajes = _normalizar_historial(historial)
    mensajes.append({"role": "user", "content": mensaje})

    cliente = Anthropic(api_key=settings.LLM_API_KEY)
    respuesta = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=700,
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
            max_output_tokens=700,
            temperature=0.25,
        ),
    )
    return (getattr(respuesta, "text", "") or "").strip()


def _resolver_proveedor():
    proveedor_preferido = (getattr(settings, "LLM_PROVIDER", "gemini") or "gemini").lower().strip()

    if proveedor_preferido == "gemini" and _gemini_configurada():
        return "gemini", _llamar_gemini
    if proveedor_preferido == "anthropic" and _anthropic_configurada():
        return "anthropic", _llamar_anthropic
    if _gemini_configurada():
        return "gemini", _llamar_gemini
    if _anthropic_configurada():
        return "anthropic", _llamar_anthropic
    return "fallback", None


def _modelo_por_proveedor(proveedor):
    if proveedor == "gemini":
        return getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite")
    if proveedor == "anthropic":
        return "claude-haiku-4-5-20251001"
    return ""


def generar_respuesta_asistente(mensaje, historial=None, usuario=None):
    """Genera una respuesta del asistente con proveedor real o fallback local."""

    historial = historial or []
    proveedor, funcion_llm = _resolver_proveedor()
    system_prompt = construir_system_prompt(usuario)

    if funcion_llm is None:
        return {
            "respuesta": _respuesta_fallback(mensaje),
            "modo": "fallback",
            "proveedor": "fallback",
        }

    try:
        texto = funcion_llm(mensaje, historial, system_prompt)
        if texto:
            return {
                "respuesta": texto,
                "modo": "ia",
                "proveedor": proveedor,
                "modelo_usado": _modelo_por_proveedor(proveedor),
            }
    except Exception:
        pass

    return {
        "respuesta": _respuesta_fallback(mensaje),
        "modo": "fallback",
        "proveedor": "fallback",
    }


@transaction.atomic
def procesar_mensaje_conversacion(*, conversacion, mensaje, usuario):
    """Persiste el mensaje del usuario, genera respuesta y guarda la respuesta."""

    mensaje = mensaje.strip()
    historial = _historial_desde_conversacion(conversacion)
    if conversacion.titulo == "Nueva conversación":
        conversacion.titulo = crear_titulo_conversacion(mensaje)
        conversacion.save(update_fields=["titulo", "fecha_actualizacion"])

    mensaje_usuario = MensajeAsistente.objects.create(
        conversacion=conversacion,
        rol=MensajeAsistente.Rol.USUARIO,
        contenido=mensaje,
    )
    resultado = generar_respuesta_asistente(mensaje, historial, usuario=usuario)
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
