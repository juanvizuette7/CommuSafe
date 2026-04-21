"""Serializers del módulo de notificaciones."""

from rest_framework import serializers

from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer de lectura de notificaciones del usuario."""

    tipo_label = serializers.SerializerMethodField()
    incidente_titulo = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            "id",
            "titulo",
            "cuerpo",
            "tipo",
            "tipo_label",
            "leida",
            "fecha_envio",
            "incidente_relacionado",
            "incidente_titulo",
            "enviada_push",
        ]
        read_only_fields = fields

    def get_tipo_label(self, obj):
        return obj.get_tipo_display()

    def get_incidente_titulo(self, obj):
        if not obj.incidente_relacionado:
            return ""
        return obj.incidente_relacionado.titulo
