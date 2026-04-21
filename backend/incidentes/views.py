"""Vistas del módulo de incidentes."""

from django.db.models import Case, Count, IntegerField, Prefetch, Value, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from usuarios.permissions import EsAdministrador

from .filters import IncidenteOrderingFilter
from .models import HistorialEstado, Incidente
from .permissions import PuedeCrearIncidente, PuedeGestionarEstadoIncidente
from .serializers import (
    AgregarEvidenciaSerializer,
    EvidenciaIncidenteSerializer,
    CambiarEstadoSerializer,
    IncidenteCreateSerializer,
    IncidenteDetailSerializer,
    IncidenteListSerializer,
)
from .services import cambiar_estado_incidente


class IncidenteViewSet(viewsets.ModelViewSet):
    """ViewSet principal de incidentes."""

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, IncidenteOrderingFilter]
    filterset_fields = ["categoria", "estado", "prioridad", "reportado_por"]
    search_fields = ["titulo", "descripcion"]
    ordering_fields = ["fecha_reporte", "prioridad"]

    def get_queryset(self):
        queryset = (
            Incidente.objects.select_related("reportado_por", "atendido_por")
            .prefetch_related(
                "evidencias",
                Prefetch("historial", queryset=HistorialEstado.objects.select_related("cambiado_por")),
            )
            .annotate(
                total_evidencias=Count("evidencias"),
                prioridad_orden=Case(
                    When(prioridad=Incidente.Prioridad.BAJA, then=Value(1)),
                    When(prioridad=Incidente.Prioridad.MEDIA, then=Value(2)),
                    When(prioridad=Incidente.Prioridad.ALTA, then=Value(3)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
        )

        usuario = self.request.user
        if usuario.es_residente:
            queryset = queryset.filter(reportado_por=usuario)

        return queryset.order_by("-fecha_reporte")

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [PuedeCrearIncidente]
        elif self.action == "destroy":
            permission_classes = [EsAdministrador]
        elif self.action == "cambiar_estado":
            permission_classes = [PuedeGestionarEstadoIncidente]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "list":
            return IncidenteListSerializer
        if self.action == "retrieve":
            return IncidenteDetailSerializer
        if self.action == "create":
            return IncidenteCreateSerializer
        return IncidenteDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        incidente = serializer.save()
        detalle = IncidenteDetailSerializer(incidente, context={"request": request})
        return Response(detalle.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        incidente = self.get_object()
        serializer = CambiarEstadoSerializer(
            data=request.data,
            context={"request": request, "incidente": incidente},
        )
        serializer.is_valid(raise_exception=True)

        incidente, _ = cambiar_estado_incidente(
            incidente=incidente,
            estado_nuevo=serializer.validated_data["estado_nuevo"],
            comentario=serializer.validated_data["comentario"],
            usuario=request.user,
        )

        incidente.refresh_from_db()
        detalle = IncidenteDetailSerializer(incidente, context={"request": request})
        return Response(
            {
                "mensaje": "El estado del incidente fue actualizado correctamente.",
                "incidente": detalle.data,
            }
        )

    @action(detail=True, methods=["post"], url_path="agregar-evidencia")
    def agregar_evidencia(self, request, pk=None):
        incidente = self.get_object()

        if request.user.es_residente and incidente.reportado_por_id != request.user.id:
            return Response(
                {"detail": "Solo puedes agregar evidencias a tus propios incidentes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AgregarEvidenciaSerializer(
            data=request.data,
            context={"request": request, "incidente": incidente},
        )
        serializer.is_valid(raise_exception=True)
        evidencia = serializer.save()

        return Response(
            {
                "mensaje": "La evidencia fue agregada correctamente.",
                "evidencia": EvidenciaIncidenteSerializer(evidencia, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )
