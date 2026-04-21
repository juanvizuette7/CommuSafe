"""Serializers del módulo de incidentes."""

from django.db import transaction
from rest_framework import serializers

from .models import EvidenciaIncidente, HistorialEstado, Incidente


class UsuarioIncidenteSerializer(serializers.Serializer):
    """Resumen de usuario para relaciones del incidente."""

    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    apellido = serializers.CharField(read_only=True)
    nombre_completo = serializers.CharField(read_only=True)
    rol = serializers.CharField(read_only=True)
    unidad_residencial = serializers.CharField(read_only=True)


class EvidenciaIncidenteSerializer(serializers.ModelSerializer):
    """Serializer de evidencias de un incidente."""

    class Meta:
        model = EvidenciaIncidente
        fields = ["id", "imagen", "descripcion", "fecha_subida"]
        read_only_fields = ["id", "fecha_subida"]


class HistorialEstadoSerializer(serializers.ModelSerializer):
    """Serializer del historial de estados."""

    cambiado_por = UsuarioIncidenteSerializer(read_only=True)
    estado_anterior_label = serializers.SerializerMethodField()
    estado_nuevo_label = serializers.SerializerMethodField()

    class Meta:
        model = HistorialEstado
        fields = [
            "id",
            "estado_anterior",
            "estado_anterior_label",
            "estado_nuevo",
            "estado_nuevo_label",
            "cambiado_por",
            "fecha_cambio",
            "comentario",
        ]
        read_only_fields = fields

    def get_estado_anterior_label(self, obj):
        if not obj.estado_anterior:
            return "Sin estado previo"
        return dict(Incidente.Estado.choices).get(obj.estado_anterior, obj.estado_anterior)

    def get_estado_nuevo_label(self, obj):
        return obj.get_estado_nuevo_display()


class IncidenteListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listados."""

    categoria_label = serializers.SerializerMethodField()
    prioridad_label = serializers.SerializerMethodField()
    estado_label = serializers.SerializerMethodField()
    reportado_por_nombre = serializers.SerializerMethodField()
    atendido_por_nombre = serializers.SerializerMethodField()
    total_evidencias = serializers.IntegerField(read_only=True)

    class Meta:
        model = Incidente
        fields = [
            "id",
            "titulo",
            "descripcion",
            "categoria",
            "categoria_label",
            "prioridad",
            "prioridad_label",
            "estado",
            "estado_label",
            "ubicacion_referencia",
            "reportado_por",
            "reportado_por_nombre",
            "atendido_por",
            "atendido_por_nombre",
            "fecha_reporte",
            "fecha_actualizacion",
            "fecha_cierre",
            "total_evidencias",
        ]
        read_only_fields = fields

    def get_categoria_label(self, obj):
        return obj.get_categoria_display()

    def get_prioridad_label(self, obj):
        return obj.get_prioridad_display()

    def get_estado_label(self, obj):
        return obj.get_estado_display()

    def get_reportado_por_nombre(self, obj):
        return obj.reportado_por.nombre_completo

    def get_atendido_por_nombre(self, obj):
        if not obj.atendido_por:
            return ""
        return obj.atendido_por.nombre_completo


class IncidenteDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle del incidente."""

    categoria_label = serializers.SerializerMethodField()
    prioridad_label = serializers.SerializerMethodField()
    estado_label = serializers.SerializerMethodField()
    reportado_por = UsuarioIncidenteSerializer(read_only=True)
    atendido_por = UsuarioIncidenteSerializer(read_only=True)
    evidencias = EvidenciaIncidenteSerializer(many=True, read_only=True)
    historial = HistorialEstadoSerializer(many=True, read_only=True)

    class Meta:
        model = Incidente
        fields = [
            "id",
            "titulo",
            "descripcion",
            "categoria",
            "categoria_label",
            "prioridad",
            "prioridad_label",
            "estado",
            "estado_label",
            "ubicacion_referencia",
            "reportado_por",
            "atendido_por",
            "fecha_reporte",
            "fecha_actualizacion",
            "fecha_cierre",
            "observaciones_cierre",
            "evidencias",
            "historial",
        ]
        read_only_fields = fields

    def get_categoria_label(self, obj):
        return obj.get_categoria_display()

    def get_prioridad_label(self, obj):
        return obj.get_prioridad_display()

    def get_estado_label(self, obj):
        return obj.get_estado_display()


class IncidenteCreateSerializer(serializers.ModelSerializer):
    """Serializer de creación del incidente con soporte de evidencias."""

    imagenes = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Incidente
        fields = [
            "id",
            "titulo",
            "descripcion",
            "categoria",
            "ubicacion_referencia",
            "imagenes",
        ]
        read_only_fields = ["id"]

    def to_internal_value(self, data):
        request = self.context.get("request")
        if request and request.FILES:
            imagenes = request.FILES.getlist("imagenes")
            if imagenes and hasattr(data, "copy"):
                data = data.copy()
                if hasattr(data, "setlist"):
                    data.setlist("imagenes", imagenes)
                else:
                    data["imagenes"] = imagenes
        return super().to_internal_value(data)

    def validate_imagenes(self, value):
        if len(value) > 3:
            raise serializers.ValidationError("Solo se permiten máximo 3 evidencias por incidente.")
        return value

    def create(self, validated_data):
        imagenes = validated_data.pop("imagenes", [])
        request = self.context["request"]
        with transaction.atomic():
            incidente = Incidente.objects.create(reportado_por=request.user, **validated_data)
            for imagen in imagenes:
                EvidenciaIncidente.objects.create(incidente=incidente, imagen=imagen)
        return incidente


class CambiarEstadoSerializer(serializers.Serializer):
    """Valida el cambio de estado de un incidente."""

    estado_nuevo = serializers.ChoiceField(choices=Incidente.Estado.choices)
    comentario = serializers.CharField(min_length=5)

    transiciones_permitidas = {
        Incidente.Estado.REGISTRADO: {Incidente.Estado.EN_PROCESO},
        Incidente.Estado.EN_PROCESO: {Incidente.Estado.RESUELTO},
        Incidente.Estado.RESUELTO: {Incidente.Estado.CERRADO},
        Incidente.Estado.CERRADO: set(),
    }

    def validate_comentario(self, value):
        comentario = value.strip()
        if len(comentario) < 5:
            raise serializers.ValidationError("El comentario debe tener al menos 5 caracteres.")
        return comentario

    def validate(self, attrs):
        incidente = self.context["incidente"]
        usuario = self.context["request"].user
        estado_nuevo = attrs["estado_nuevo"]

        if incidente.estado == estado_nuevo:
            raise serializers.ValidationError(
                {"estado_nuevo": "El incidente ya se encuentra en ese estado."}
            )

        if estado_nuevo not in self.transiciones_permitidas.get(incidente.estado, set()):
            raise serializers.ValidationError(
                {
                    "estado_nuevo": (
                        f"No se permite cambiar el estado de {incidente.get_estado_display()} "
                        f"a {dict(Incidente.Estado.choices).get(estado_nuevo, estado_nuevo)}."
                    )
                }
            )

        if estado_nuevo == Incidente.Estado.CERRADO and not usuario.es_administrador:
            raise serializers.ValidationError(
                {"estado_nuevo": "Solo un administrador puede cerrar un incidente."}
            )

        return attrs


class AgregarEvidenciaSerializer(serializers.ModelSerializer):
    """Serializer para agregar una evidencia adicional a un incidente."""

    class Meta:
        model = EvidenciaIncidente
        fields = ["id", "imagen", "descripcion", "fecha_subida"]
        read_only_fields = ["id", "fecha_subida"]

    def validate(self, attrs):
        incidente = self.context["incidente"]
        if incidente.evidencias.count() >= 3:
            raise serializers.ValidationError(
                {"imagen": "El incidente ya tiene el máximo permitido de 3 evidencias."}
            )
        if incidente.estado == Incidente.Estado.CERRADO:
            raise serializers.ValidationError(
                {"imagen": "No se pueden agregar evidencias a un incidente cerrado."}
            )
        return attrs

    def create(self, validated_data):
        incidente = self.context["incidente"]
        return EvidenciaIncidente.objects.create(incidente=incidente, **validated_data)
