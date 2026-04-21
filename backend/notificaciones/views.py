"""Vistas base del módulo de notificaciones."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class NotificacionesRootAPIView(APIView):
    """Punto de entrada del servicio interno de notificaciones."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "modulo": "notificaciones",
                "mensaje": "El servicio interno de notificaciones está disponible para eventos del sistema.",
            }
        )
