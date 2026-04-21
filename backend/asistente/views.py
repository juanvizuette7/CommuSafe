"""Vistas del módulo de asistente virtual."""

from anthropic import Anthropic
from django.conf import settings
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView


CONOCIMIENTO_REMANSOS = """
Conjunto residencial: Remansos del Norte.
Administración: atención de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sábados de 8:00 a. m. a 12:00 m.
Portería y vigilancia: atención permanente 24/7.
Horarios de áreas comunes: de 6:00 a. m. a 10:00 p. m.
Normas de convivencia base: respetar horarios de descanso entre 10:00 p. m. y 6:00 a. m., recoger excrementos de mascotas, usar correa en zonas comunes, no obstruir pasillos ni escaleras, respetar el reglamento de uso de zonas comunes.
Procedimiento de incidentes en CommuSafe: el residente reporta, vigilancia atiende, administración supervisa y puede cerrar el caso.
Emergencias: contactar portería de inmediato y, si la situación es crítica, llamar a la línea 123.
Cuotas de administración: se consultan y gestionan con administración; si el usuario requiere valores exactos o estado de cartera, debe contactar directamente a la administración.
Uso de CommuSafe: permite iniciar sesión, reportar incidentes, ver notificaciones, consultar estados y recibir orientación básica del asistente.
Si una pregunta sale de este alcance, el asistente debe decirlo claramente y sugerir contactar a la administración.
""".strip()


SYSTEM_PROMPT = f"""
Eres el asistente virtual oficial de CommuSafe para el conjunto residencial Remansos del Norte.
Respondes siempre en español, con tono amable, claro y conciso.
Solo puedes responder con base en esta información autorizada:
{CONOCIMIENTO_REMANSOS}
No inventes políticas, valores, nombres de personas, multas ni decisiones administrativas.
Si la información no está disponible o requiere confirmación humana, indica que el usuario debe contactar a la administración o a portería.
Evita respuestas largas y mantén el foco en ayudar al residente dentro del contexto del conjunto y la app.
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


def _api_llm_configurada():
    valor = (settings.LLM_API_KEY or "").strip()
    return bool(valor and "REEMPLAZAR" not in valor.upper())


def _normalizar_historial(historial):
    mensajes = []
    for item in historial[-8:]:
        rol = "assistant" if item["rol"] in {"assistant", "asistente"} else "user"
        mensajes.append({"role": rol, "content": item["contenido"].strip()})
    return mensajes


def _respuesta_fallback(mensaje):
    texto = mensaje.lower()

    if any(palabra in texto for palabra in ["horario", "horarios", "salón", "zona común", "zonas comunes"]):
        return (
            "En Remansos del Norte, las áreas comunes funcionan de 6:00 a. m. a 10:00 p. m. "
            "La administración atiende de lunes a viernes de 8:00 a. m. a 5:00 p. m. y sábados de 8:00 a. m. a 12:00 m."
        )
    if any(palabra in texto for palabra in ["emergencia", "gas", "incendio", "ambulancia", "urgencia"]):
        return (
            "Si se trata de una emergencia, contacta de inmediato a portería y, si hay riesgo para la vida o la seguridad, "
            "llama también a la línea 123. Si puedes, registra el incidente en CommuSafe para dejar trazabilidad."
        )
    if any(palabra in texto for palabra in ["cuota", "administración", "cartera", "pago"]):
        return (
            "Las cuotas de administración y el estado de cartera se gestionan directamente con la administración del conjunto. "
            "Si necesitas el valor exacto o confirmar un pago, debes comunicarte con administración."
        )
    if any(palabra in texto for palabra in ["norma", "convivencia", "ruido", "mascota", "reglamento"]):
        return (
            "Las normas básicas de convivencia incluyen respetar el horario de descanso entre 10:00 p. m. y 6:00 a. m., "
            "usar correa para las mascotas en zonas comunes, recoger sus residuos y no obstruir pasillos o escaleras."
        )
    if any(palabra in texto for palabra in ["app", "commusafe", "incidente", "reporte", "notificación"]):
        return (
            "Con CommuSafe puedes reportar incidentes, consultar su estado, recibir notificaciones y comunicarte mejor con vigilancia y administración."
        )

    return (
        "No tengo una respuesta confirmada para esa consulta dentro de la información autorizada de Remansos del Norte. "
        "Te recomiendo contactar directamente a la administración para obtener orientación precisa."
    )


def _extraer_texto_anthropic(respuesta):
    bloques = getattr(respuesta, "content", []) or []
    textos = [getattr(bloque, "text", "").strip() for bloque in bloques if getattr(bloque, "text", "").strip()]
    return "\n".join(textos).strip()


class ChatAsistenteView(APIView):
    """Endpoint principal del asistente virtual."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatAsistenteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mensaje = serializer.validated_data["mensaje"].strip()
        historial = serializer.validated_data.get("historial", [])

        if not _api_llm_configurada():
            return Response(
                {
                    "respuesta": _respuesta_fallback(mensaje),
                    "modo": "fallback",
                },
                status=status.HTTP_200_OK,
            )

        mensajes = _normalizar_historial(historial)
        mensajes.append({"role": "user", "content": mensaje})

        try:
            cliente = Anthropic(api_key=settings.LLM_API_KEY)
            respuesta = cliente.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=mensajes,
            )
            texto = _extraer_texto_anthropic(respuesta)
            if not texto:
                texto = _respuesta_fallback(mensaje)
                modo = "fallback"
            else:
                modo = "ia"
        except Exception:
            texto = _respuesta_fallback(mensaje)
            modo = "fallback"

        return Response(
            {
                "respuesta": texto,
                "modo": modo,
            },
            status=status.HTTP_200_OK,
        )
