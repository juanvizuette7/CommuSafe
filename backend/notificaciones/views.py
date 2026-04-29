"""Vistas del módulo de notificaciones."""

from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from usuarios.permissions import EsAdministradorOVigilante

from .models import Notificacion
from .serializers import (
    AvisoComunitarioSerializer,
    DestinatarioAvisoSerializer,
    NotificacionSerializer,
)
from .services import notificar_aviso_comunitario, usuarios_disponibles_para_aviso


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """Permite consultar las notificaciones propias del usuario autenticado."""

    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notificacion.objects.filter(destinatario=self.request.user).select_related(
            "incidente_relacionado"
        )

    @action(detail=False, methods=["get"], url_path="no-leidas-count")
    def no_leidas_count(self, request):
        total = self.get_queryset().filter(leida=False).count()
        return Response({"no_leidas": total})

    @action(detail=False, methods=["get"], url_path="avisos-vigentes")
    def avisos_vigentes(self, request):
        fecha_limite = timezone.now() - timedelta(days=7)
        queryset = self.get_queryset().filter(
            tipo__in=[Notificacion.Tipo.AVISO_ADMIN, Notificacion.Tipo.EMERGENCIA],
            leida=False,
            fecha_envio__gte=fecha_limite,
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="leer")
    def leer(self, request, pk=None):
        notificacion = self.get_object()
        if not notificacion.leida:
            notificacion.leida = True
            notificacion.save(update_fields=["leida"])
        return Response({"mensaje": "La notificación fue marcada como leída."})

    @action(detail=False, methods=["post"], url_path="leer-todas")
    def leer_todas(self, request):
        actualizadas = self.get_queryset().filter(leida=False).update(leida=True)
        return Response(
            {
                "mensaje": "Todas las notificaciones pendientes fueron marcadas como leídas.",
                "total_actualizadas": actualizadas,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="avisos",
        permission_classes=[permissions.IsAuthenticated, EsAdministradorOVigilante],
    )
    def avisos(self, request):
        serializer = AvisoComunitarioSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        resultado = notificar_aviso_comunitario(**serializer.validated_data)
        return Response(
            {
                "mensaje": "El aviso fue enviado correctamente.",
                **resultado,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="destinatarios-avisos",
        permission_classes=[permissions.IsAuthenticated, EsAdministradorOVigilante],
    )
    def destinatarios_avisos(self, request):
        usuarios = usuarios_disponibles_para_aviso(request.user)
        serializer = DestinatarioAvisoSerializer(usuarios, many=True)
        por_rol = {
            "residentes": [],
            "vigilantes": [],
            "administradores": [],
        }
        for usuario in serializer.data:
            if usuario["rol"] == "RESIDENTE":
                por_rol["residentes"].append(usuario)
            elif usuario["rol"] == "VIGILANTE":
                por_rol["vigilantes"].append(usuario)
            elif usuario["rol"] == "ADMINISTRADOR":
                por_rol["administradores"].append(usuario)
        return Response(por_rol)
