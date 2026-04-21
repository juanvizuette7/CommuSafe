"""Vistas de autenticación y gestión de usuarios."""

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .permissions import EsAdministrador
from .serializers import (
    CambioRolSerializer,
    CommuSafeTokenObtainPairSerializer,
    FCMTokenSerializer,
    UsuarioAdminUpdateSerializer,
    UsuarioCreateSerializer,
    UsuarioSerializer,
    UsuarioUpdateSerializer,
)


Usuario = get_user_model()


class InicioSesionView(TokenObtainPairView):
    """Endpoint de autenticación JWT."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CommuSafeTokenObtainPairSerializer


class RenovarTokenView(TokenRefreshView):
    """Endpoint para renovación de tokens."""

    permission_classes = [permissions.AllowAny]


class PerfilPropioView(APIView):
    """Consulta y actualización del perfil autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def put(self, request):
        serializer = UsuarioUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UsuarioSerializer(request.user, context={"request": request}).data)


class ActualizarFCMTokenView(APIView):
    """Actualiza el token FCM del usuario autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FCMTokenSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"mensaje": "Token de Firebase actualizado correctamente."})

    def put(self, request):
        return self.post(request)


class UsuarioViewSet(viewsets.ModelViewSet):
    """Gestión administrativa de usuarios."""

    queryset = Usuario.objects.all().order_by("-fecha_registro")
    permission_classes = [EsAdministrador]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rol", "activo", "is_staff"]
    search_fields = ["email", "nombre", "apellido", "unidad_residencial"]
    ordering_fields = ["fecha_registro", "nombre", "apellido", "email"]

    def get_serializer_class(self):
        if self.action == "create":
            return UsuarioCreateSerializer
        if self.action in {"update", "partial_update"}:
            return UsuarioAdminUpdateSerializer
        return UsuarioSerializer

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        usuario.activo = False
        usuario.save(update_fields=["activo"])
        return Response(
            {"mensaje": "La cuenta fue desactivada en lugar de eliminarse físicamente."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="activar")
    def activar(self, request, pk=None):
        usuario = self.get_object()
        usuario.activo = True
        usuario.save(update_fields=["activo"])
        return Response({"mensaje": "La cuenta fue activada correctamente."})

    @action(detail=True, methods=["post"], url_path="desactivar")
    def desactivar(self, request, pk=None):
        usuario = self.get_object()
        usuario.activo = False
        usuario.save(update_fields=["activo"])
        return Response({"mensaje": "La cuenta fue desactivada correctamente."})

    @action(detail=True, methods=["post"], url_path="cambiar-rol")
    def cambiar_rol(self, request, pk=None):
        usuario = self.get_object()
        serializer = CambioRolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario.rol = serializer.validated_data["rol"]
        usuario.is_staff = usuario.rol == Usuario.Rol.ADMINISTRADOR or usuario.is_superuser
        usuario.full_clean()
        usuario.save(update_fields=["rol", "is_staff"])
        return Response(
            {
                "mensaje": "El rol del usuario fue actualizado correctamente.",
                "usuario": UsuarioSerializer(usuario, context={"request": request}).data,
            }
        )
