"""Vistas base del módulo de incidentes."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class IncidentesRootAPIView(APIView):
    """Punto de entrada temporal del módulo de incidentes."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "modulo": "incidentes",
                "mensaje": "El módulo de incidentes está preparado para el Sprint 2.",
            }
        )
