"""Serializers del asistente virtual."""

from rest_framework import serializers

from .models import ConversacionAsistente, MensajeAsistente


class HistorialMensajeSerializer(serializers.Serializer):
    """Valida cada mensaje del historial reciente del endpoint legado."""

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
    """Valida la entrada del endpoint legado del chat."""

    mensaje = serializers.CharField(max_length=2000)
    historial = HistorialMensajeSerializer(many=True, required=False)

    def validate_historial(self, value):
        return value[-8:]


class MensajeAsistenteSerializer(serializers.ModelSerializer):
    """Representación de un mensaje persistido."""

    rol_label = serializers.CharField(source="get_rol_display", read_only=True)

    class Meta:
        model = MensajeAsistente
        fields = ["id", "conversacion", "rol", "rol_label", "contenido", "fecha_creacion"]
        read_only_fields = fields


class ConversacionAsistenteSerializer(serializers.ModelSerializer):
    """Resumen de conversaciones del usuario."""

    total_mensajes = serializers.SerializerMethodField()
    ultimo_mensaje = serializers.SerializerMethodField()

    class Meta:
        model = ConversacionAsistente
        fields = [
            "id",
            "titulo",
            "fecha_creacion",
            "fecha_actualizacion",
            "total_mensajes",
            "ultimo_mensaje",
        ]
        read_only_fields = ["id", "fecha_creacion", "fecha_actualizacion", "total_mensajes", "ultimo_mensaje"]

    def get_ultimo_mensaje(self, obj):
        mensaje = obj.mensajes.order_by("-fecha_creacion").first()
        return mensaje.contenido[:160] if mensaje else ""

    def get_total_mensajes(self, obj):
        total = getattr(obj, "total_mensajes", None)
        return total if total is not None else obj.mensajes.count()


class ConversacionCreateSerializer(serializers.ModelSerializer):
    """Permite crear una conversación vacía."""

    titulo = serializers.CharField(max_length=90, required=False, allow_blank=True)

    class Meta:
        model = ConversacionAsistente
        fields = ["id", "titulo", "fecha_creacion", "fecha_actualizacion"]
        read_only_fields = ["id", "fecha_creacion", "fecha_actualizacion"]

    def validate_titulo(self, value):
        value = value.strip()
        return value or "Nueva conversación"


class ConversacionTituloSerializer(serializers.Serializer):
    """Valida cambio manual de título."""

    titulo = serializers.CharField(max_length=90, min_length=3)

    def validate_titulo(self, value):
        return value.strip()


class EnviarMensajeSerializer(serializers.Serializer):
    """Valida envío de un mensaje dentro de una conversación."""

    mensaje = serializers.CharField(max_length=2000, min_length=1)

    def validate_mensaje(self, value):
        return value.strip()
