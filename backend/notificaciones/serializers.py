"""Serializers del módulo de notificaciones."""

from rest_framework import serializers

from usuarios.models import Usuario

from .models import Notificacion
from .services import AudienciaAviso, usuarios_disponibles_para_aviso


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
    destinatarios_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    tipo = serializers.ChoiceField(
        choices=[
            (Notificacion.Tipo.AVISO_ADMIN, "Aviso administrativo"),
            (Notificacion.Tipo.EMERGENCIA, "Alerta de emergencia"),
        ],
        default=Notificacion.Tipo.AVISO_ADMIN,
    )

    def validate(self, attrs):
        usuario = self.context["request"].user
        audiencia = attrs["audiencia"]
        destinatarios_ids = attrs.pop("destinatarios_ids", [])

        if usuario.es_vigilante and audiencia not in {
            AudienciaAviso.RESIDENTES,
            AudienciaAviso.ESPECIFICOS,
        }:
            raise serializers.ValidationError(
                "El personal de vigilancia solo puede enviar avisos a residentes."
            )

        if audiencia == AudienciaAviso.ESPECIFICOS:
            if not destinatarios_ids:
                raise serializers.ValidationError(
                    {"destinatarios_ids": "Selecciona al menos un destinatario específico."}
                )

            disponibles = usuarios_disponibles_para_aviso(usuario)
            destinatarios = list(disponibles.filter(id__in=destinatarios_ids))
            encontrados = {destinatario.id for destinatario in destinatarios}
            faltantes = [id_usuario for id_usuario in destinatarios_ids if id_usuario not in encontrados]
            if faltantes:
                raise serializers.ValidationError(
                    {"destinatarios_ids": "Uno o más destinatarios no existen o no están permitidos."}
                )
            attrs["destinatarios"] = destinatarios
        else:
            attrs["destinatarios"] = None

        attrs["titulo"] = attrs["titulo"].strip()
        attrs["cuerpo"] = attrs["cuerpo"].strip()
        return attrs


class DestinatarioAvisoSerializer(serializers.ModelSerializer):
    """Resumen de usuario activo seleccionable como destinatario de avisos."""

    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "nombre",
            "apellido",
            "nombre_completo",
            "rol",
            "telefono",
            "unidad_residencial",
        ]
        read_only_fields = fields
