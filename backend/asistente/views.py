"""Vistas base del módulo de asistente virtual."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AsistenteRootAPIView(APIView):
    """Punto de entrada temporal del módulo de asistente."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "modulo": "asistente",
                "mensaje": "El módulo de asistente virtual está preparado para el Sprint 3.",
            }
        )
