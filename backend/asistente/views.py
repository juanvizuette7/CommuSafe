"""Vistas del módulo de asistente virtual."""

from django.db.models import Count, Prefetch
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConversacionAsistente, MensajeAsistente
from .serializers import (
    ChatAsistenteSerializer,
    ConversacionAsistenteSerializer,
    ConversacionCreateSerializer,
    ConversacionTituloSerializer,
    EnviarMensajeSerializer,
    HistorialMensajeSerializer,
    MensajeAsistenteSerializer,
)
from .services import (
    _api_llm_configurada,
    _extraer_texto_anthropic,
    _modelo_por_proveedor,
    _normalizar_historial,
    _resolver_proveedor,
    _respuesta_fallback,
    generar_respuesta_asistente,
    local_engine_stats,
    procesar_mensaje_conversacion,
)


class ChatAsistenteView(APIView):
    """Endpoint legado del asistente virtual sin persistencia de conversación."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatAsistenteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mensaje = serializer.validated_data["mensaje"].strip()
        historial = serializer.validated_data.get("historial", [])
        return Response(
            generar_respuesta_asistente(mensaje, historial, usuario=request.user),
            status=status.HTTP_200_OK,
        )


class ChatHealthView(APIView):
    """Expone el estado de configuración del proveedor de IA."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        proveedor, funcion_llm = _resolver_proveedor()
        return Response(
            {
                "proveedor_activo": proveedor,
                "modelo": _modelo_por_proveedor(proveedor),
                "configurado": bool(funcion_llm),
                "arquitectura": "hibrida_local_primero",
                "motor_local": local_engine_stats(),
            },
            status=status.HTTP_200_OK,
        )


class ConversacionAsistenteViewSet(viewsets.ModelViewSet):
    """CRUD y acciones del historial persistente del asistente."""

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        mensajes_prefetch = Prefetch(
            "mensajes",
            queryset=MensajeAsistente.objects.order_by("fecha_creacion"),
        )
        return (
            ConversacionAsistente.objects.filter(usuario=self.request.user)
            .annotate(total_mensajes=Count("mensajes"))
            .prefetch_related(mensajes_prefetch)
            .order_by("-fecha_actualizacion")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ConversacionCreateSerializer
        if self.action == "actualizar_titulo":
            return ConversacionTituloSerializer
        return ConversacionAsistenteSerializer

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=["get"], url_path="mensajes")
    def mensajes(self, request, pk=None):
        conversacion = self.get_object()
        serializer = MensajeAsistenteSerializer(conversacion.mensajes.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="enviar")
    def enviar(self, request, pk=None):
        conversacion = self.get_object()
        serializer = EnviarMensajeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resultado = procesar_mensaje_conversacion(
            conversacion=conversacion,
            mensaje=serializer.validated_data["mensaje"],
            usuario=request.user,
        )
        return Response(
            {
                "conversacion": ConversacionAsistenteSerializer(resultado["conversacion"]).data,
                "mensaje_usuario": MensajeAsistenteSerializer(resultado["mensaje_usuario"]).data,
                "mensaje_asistente": MensajeAsistenteSerializer(resultado["mensaje_asistente"]).data,
                "respuesta": resultado["respuesta"],
                "modo": resultado["modo"],
                "proveedor": resultado["proveedor"],
                "modelo_usado": resultado.get("modelo_usado", ""),
                "confianza": resultado.get("confianza", 0),
                "intencion": resultado.get("intencion", ""),
                "metodo": resultado.get("metodo", ""),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["patch"], url_path="titulo")
    def actualizar_titulo(self, request, pk=None):
        conversacion = self.get_object()
        serializer = ConversacionTituloSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversacion.titulo = serializer.validated_data["titulo"]
        conversacion.save(update_fields=["titulo", "fecha_actualizacion"])
        return Response(
            ConversacionAsistenteSerializer(conversacion).data,
            status=status.HTTP_200_OK,
        )
