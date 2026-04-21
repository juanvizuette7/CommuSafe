"""Vistas del módulo de notificaciones."""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notificacion
from .serializers import NotificacionSerializer


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
