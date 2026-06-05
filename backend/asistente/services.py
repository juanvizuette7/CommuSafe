"""Servicios del asistente virtual persistente."""

import re
import time
from decimal import Decimal, InvalidOperation

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

from .knowledge_base import render_knowledge_base
from .local_engine import local_engine_stats, resolve_local_answer
from .models import AsistenteRespuestaLog, ConversacionAsistente, MensajeAsistente


CONOCIMIENTO_REMANSOS = render_knowledge_base()


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


def _decimal_confianza(valor):
    try:
        return Decimal(str(round(float(valor or 0), 4)))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _estimar_tokens(texto):
    if not texto:
        return 0
    return max(1, int(len(str(texto).split()) * 1.35))


def _respuesta_segura_controlada():
    return (
        "No encuentro informacion verificada suficiente en CommuSafe para responder esa consulta con precision. "
        "Te recomiendo validarlo directamente con administracion para evitar datos incorrectos."
    )


def _registrar_respuesta_log(*, mensaje, resultado, usuario=None, conversacion=None):
    """Guarda trazabilidad tecnica sin interrumpir el chat si falla el registro."""

    try:
        AsistenteRespuestaLog.objects.create(
            usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
            conversacion=conversacion,
            mensaje=mensaje[:4000],
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
            "verified": local_result.get("verified", False),
            "options": local_result.get("options", []),
            "score_parts": local_result.get("score_parts", {}),
            "updated_at": local_result.get("updated_at", ""),
        },
    }


def generar_respuesta_asistente(mensaje, historial=None, usuario=None, conversacion=None):
    """Genera respuesta hibrida: local verificado primero, IA solo como respaldo."""

    inicio = time.perf_counter()
    historial = historial or []
    rol = getattr(usuario, "rol", "RESIDENTE") if usuario else "RESIDENTE"
    local_result = resolve_local_answer(mensaje, rol)

    if local_result["action"] in {"answer", "clarify", "safe"}:
        resultado = _payload_desde_local(local_result)
        _registrar_respuesta_log(
            mensaje=mensaje,
            resultado=resultado,
            usuario=usuario,
            conversacion=conversacion,
        )
        return resultado

    proveedor, funcion_llm = _resolver_proveedor()
    system_prompt = construir_system_prompt(usuario)

    if funcion_llm is not None:
        try:
            texto = _limpiar_respuesta_ia(funcion_llm(mensaje, historial, system_prompt))
            if texto:
                latencia_ms = int((time.perf_counter() - inicio) * 1000)
                resultado = {
                    "respuesta": texto,
                    "modo": "ia",
                    "proveedor": proveedor,
                    "modelo_usado": _modelo_por_proveedor(proveedor),
                    "confianza": local_result.get("confidence", 0),
                    "intencion": local_result.get("intent", "respaldo_generativo"),
                    "categoria": local_result.get("category", "respaldo_generativo"),
                    "metodo": "ia_con_contexto_verificado",
                    "requiere_validacion": True,
                    "latencia_ms": latencia_ms,
                    "tokens_entrada": _estimar_tokens(system_prompt) + _estimar_tokens(mensaje),
                    "tokens_salida": _estimar_tokens(texto),
                    "metadata": {
                        "local_confidence": local_result.get("confidence", 0),
                        "local_method": local_result.get("method", ""),
                        "tokens_estimados": True,
                    },
                }
                _registrar_respuesta_log(
                    mensaje=mensaje,
                    resultado=resultado,
                    usuario=usuario,
                    conversacion=conversacion,
                )
                return resultado
        except Exception as exc:
            local_result["llm_error"] = str(exc)

    resultado = {
        "respuesta": _respuesta_segura_controlada(),
        "modo": "segura",
        "proveedor": "local",
        "modelo_usado": "commusafe-local-tfidf-v1",
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
            },
            "llm_disponible": bool(funcion_llm),
            "llm_error": local_result.get("llm_error", ""),
        },
    }
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
