"""Serializers del módulo de notificaciones."""

from rest_framework import serializers

from .models import Notificacion
from .services import AudienciaAviso


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


class AvisoComunitarioSerializer(serializers.Serializer):
    """Valida la creación manual de avisos comunitarios."""

    titulo = serializers.CharField(max_length=150, min_length=5)
    cuerpo = serializers.CharField(min_length=10, max_length=1200)
    audiencia = serializers.ChoiceField(choices=AudienciaAviso.CHOICES)
    tipo = serializers.ChoiceField(
        choices=[
            (Notificacion.Tipo.AVISO_ADMIN, "Aviso administrativo"),
            (Notificacion.Tipo.EMERGENCIA, "Alerta de emergencia"),
        ],
        default=Notificacion.Tipo.AVISO_ADMIN,
    )

    def validate(self, attrs):
        usuario = self.context["request"].user
        if usuario.es_vigilante and attrs["audiencia"] != AudienciaAviso.RESIDENTES:
            raise serializers.ValidationError(
                "El personal de vigilancia solo puede enviar avisos a residentes."
            )
        attrs["titulo"] = attrs["titulo"].strip()
        attrs["cuerpo"] = attrs["cuerpo"].strip()
        return attrs
