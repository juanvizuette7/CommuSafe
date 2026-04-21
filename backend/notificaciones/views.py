"""Vistas base del módulo de notificaciones."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class NotificacionesRootAPIView(APIView):
    """Punto de entrada temporal del módulo de notificaciones."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "modulo": "notificaciones",
                "mensaje": "El módulo de notificaciones está preparado para el Sprint 3.",
            }
        )
