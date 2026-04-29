"""Vistas del modulo de asistente virtual."""

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
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView


CONOCIMIENTO_REMANSOS = """
Conjunto residencial: Remansos del Norte.
Administracion: atencion de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sabados de 8:00 a. m. a 12:00 m.
Porteria y vigilancia: atencion permanente 24/7.
Horarios de areas comunes: de 6:00 a. m. a 10:00 p. m.
Normas de convivencia base: respetar horarios de descanso entre 10:00 p. m. y 6:00 a. m., recoger excrementos de mascotas, usar correa en zonas comunes, no obstruir pasillos ni escaleras, respetar el reglamento de uso de zonas comunes.
Procedimiento de incidentes en CommuSafe: el residente reporta, vigilancia atiende, administracion supervisa y puede cerrar el caso.
Emergencias: contactar porteria de inmediato y, si la situacion es critica, llamar a la linea 123.
Cuotas de administracion: se consultan y gestionan con administracion; si el usuario requiere valores exactos o estado de cartera, debe contactar directamente a la administracion.
Uso de CommuSafe: permite iniciar sesion, reportar incidentes, ver notificaciones, consultar estados y recibir orientacion basica del asistente.
Si una pregunta sale de este alcance, el asistente debe decirlo claramente y sugerir contactar a la administracion.
""".strip()


SYSTEM_PROMPT = f"""
Eres el asistente virtual oficial de CommuSafe para el conjunto residencial Remansos del Norte.
Respondes siempre en espanol, con tono amable, claro y conciso.
Solo puedes responder con base en esta informacion autorizada:
{CONOCIMIENTO_REMANSOS}
No inventes politicas, valores, nombres de personas, multas ni decisiones administrativas.
Si la informacion no esta disponible o requiere confirmacion humana, indica que el usuario debe contactar a la administracion o a porteria.
Evita respuestas largas y manten el foco en ayudar al residente dentro del contexto del conjunto y la app.
""".strip()


class HistorialMensajeSerializer(serializers.Serializer):
    """Valida cada mensaje del historial reciente."""

    rol = serializers.ChoiceField(choices=["user", "assistant", "usuario", "asistente"])
    contenido = serializers.CharField(max_length=2000, required=False, allow_blank=False)
    mensaje = serializers.CharField(max_length=2000, required=False, allow_blank=False)

    def validate(self, attrs):
        contenido = attrs.get("contenido") or attrs.get("mensaje")
        if not contenido:
            raise serializers.ValidationError("Cada mensaje del historial debe incluir contenido.")
        attrs["contenido"] = contenido.strip()
        return attrs


class ChatAsistenteSerializer(serializers.Serializer):
    """Valida la entrada del chat del asistente."""

    mensaje = serializers.CharField(max_length=2000)
    historial = HistorialMensajeSerializer(many=True, required=False)

    def validate_historial(self, value):
        return value[-8:]


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
    for item in historial[-8:]:
        rol = "assistant" if item["rol"] in {"assistant", "asistente"} else "user"
        mensajes.append({"role": rol, "content": item["contenido"].strip()})
    return mensajes


def _normalizar_historial_gemini(historial, mensaje_actual):
    lineas = []
    for item in historial[-8:]:
        rol = "Asistente" if item["rol"] in {"assistant", "asistente"} else "Usuario"
        lineas.append(f"{rol}: {item['contenido'].strip()}")
    lineas.append(f"Usuario: {mensaje_actual}")
    return "\n".join(lineas)


def _respuesta_fallback(mensaje):
    texto = mensaje.lower()

    if any(palabra in texto for palabra in ["horario", "horarios", "salon", "zona comun", "zonas comunes"]):
        return (
            "En Remansos del Norte, las areas comunes funcionan de 6:00 a. m. a 10:00 p. m. "
            "La administracion atiende de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sabados de 8:00 a. m. a 12:00 m."
        )
    if any(palabra in texto for palabra in ["emergencia", "gas", "incendio", "ambulancia", "urgencia"]):
        return (
            "Si se trata de una emergencia, contacta de inmediato a porteria y, si hay riesgo para la vida o la seguridad, "
            "llama tambien a la linea 123. Si puedes, registra el incidente en CommuSafe para dejar trazabilidad."
        )
    if any(palabra in texto for palabra in ["cuota", "administracion", "cartera", "pago"]):
        return (
            "Las cuotas de administracion y el estado de cartera se gestionan directamente con la administracion del conjunto. "
            "Si necesitas el valor exacto o confirmar un pago, debes comunicarte con administracion."
        )
    if any(palabra in texto for palabra in ["norma", "convivencia", "ruido", "mascota", "reglamento"]):
        return (
            "Las normas basicas de convivencia incluyen respetar el horario de descanso entre 10:00 p. m. y 6:00 a. m., "
            "usar correa para las mascotas en zonas comunes, recoger sus residuos y no obstruir pasillos o escaleras."
        )
    if any(palabra in texto for palabra in ["app", "commusafe", "incidente", "reporte", "notificacion"]):
        return (
            "Con CommuSafe puedes reportar incidentes, consultar su estado, recibir notificaciones y comunicarte mejor con vigilancia y administracion."
        )

    return (
        "No tengo una respuesta confirmada para esa consulta dentro de la informacion autorizada de Remansos del Norte. "
        "Te recomiendo contactar directamente a la administracion para obtener orientacion precisa."
    )


def _extraer_texto_anthropic(respuesta):
    bloques = getattr(respuesta, "content", []) or []
    textos = [getattr(bloque, "text", "").strip() for bloque in bloques if getattr(bloque, "text", "").strip()]
    return "\n".join(textos).strip()


def _llamar_anthropic(mensaje, historial):
    mensajes = _normalizar_historial(historial)
    mensajes.append({"role": "user", "content": mensaje})

    cliente = Anthropic(api_key=settings.LLM_API_KEY)
    respuesta = cliente.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=mensajes,
    )
    return _extraer_texto_anthropic(respuesta)


def _llamar_gemini(mensaje, historial):
    cliente = genai.Client(api_key=settings.GEMINI_API_KEY)
    contenido = _normalizar_historial_gemini(historial, mensaje)
    respuesta = cliente.models.generate_content(
        model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=contenido,
        config=genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=600,
            temperature=0.3,
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


def generar_respuesta_asistente(mensaje, historial=None):
    """Genera una respuesta del asistente con proveedor real o fallback local."""

    historial = historial or []
    proveedor, funcion_llm = _resolver_proveedor()

    if funcion_llm is None:
        return {
            "respuesta": _respuesta_fallback(mensaje),
            "modo": "fallback",
            "proveedor": "fallback",
        }

    try:
        texto = funcion_llm(mensaje, historial)
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


class ChatAsistenteView(APIView):
    """Endpoint principal del asistente virtual."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatAsistenteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mensaje = serializer.validated_data["mensaje"].strip()
        historial = serializer.validated_data.get("historial", [])
        return Response(generar_respuesta_asistente(mensaje, historial), status=status.HTTP_200_OK)


class ChatHealthView(APIView):
    """Expone el estado de configuracion del proveedor de IA."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        proveedor, funcion_llm = _resolver_proveedor()
        return Response(
            {
                "proveedor_activo": proveedor,
                "modelo": _modelo_por_proveedor(proveedor),
                "configurado": bool(funcion_llm),
            },
            status=status.HTTP_200_OK,
        )
