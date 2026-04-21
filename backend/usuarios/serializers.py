"""Serializers de la app de usuarios."""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer de lectura del usuario."""

    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "nombre",
            "apellido",
            "nombre_completo",
            "unidad_residencial",
            "rol",
            "telefono",
            "foto_perfil",
            "activo",
            "fecha_registro",
        ]
        read_only_fields = ["id", "email", "rol", "activo", "fecha_registro"]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer de creación de usuarios."""

    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "nombre",
            "apellido",
            "unidad_residencial",
            "rol",
            "telefono",
            "foto_perfil",
            "password",
            "activo",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        email = value.lower().strip()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email

    def validate(self, attrs):
        rol = attrs.get("rol", Usuario.Rol.RESIDENTE)
        unidad = (attrs.get("unidad_residencial", "") or "").strip()
        if rol == Usuario.Rol.RESIDENTE and not unidad:
            raise serializers.ValidationError(
                {"unidad_residencial": "La unidad residencial es obligatoria para residentes."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        if validated_data.get("rol") == Usuario.Rol.ADMINISTRADOR:
            validated_data["is_staff"] = True
        return Usuario.objects.create_user(password=password, **validated_data)


class UsuarioAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer de actualización administrativa de usuarios."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        required=False,
        allow_blank=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = Usuario
        fields = [
            "email",
            "nombre",
            "apellido",
            "unidad_residencial",
            "rol",
            "telefono",
            "foto_perfil",
            "password",
            "activo",
        ]

    def validate_email(self, value):
        email = value.lower().strip()
        queryset = Usuario.objects.filter(email__iexact=email)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email

    def validate(self, attrs):
        rol = attrs.get("rol", self.instance.rol)
        unidad = (attrs.get("unidad_residencial", self.instance.unidad_residencial) or "").strip()
        if rol == Usuario.Rol.RESIDENTE and not unidad:
            raise serializers.ValidationError(
                {"unidad_residencial": "La unidad residencial es obligatoria para residentes."}
            )
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.is_staff = instance.rol == Usuario.Rol.ADMINISTRADOR or instance.is_superuser
        if password:
            instance.set_password(password)
        instance.full_clean()
        instance.save()
        return instance


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializer de actualización del perfil propio."""

    class Meta:
        model = Usuario
        fields = ["nombre", "apellido", "unidad_residencial", "telefono", "foto_perfil"]

    def validate(self, attrs):
        usuario = self.instance
        unidad = (attrs.get("unidad_residencial", usuario.unidad_residencial) or "").strip()
        if usuario.es_residente and not unidad:
            raise serializers.ValidationError(
                {"unidad_residencial": "La unidad residencial es obligatoria para residentes."}
            )
        return attrs


class FCMTokenSerializer(serializers.ModelSerializer):
    """Serializer para actualizar el token de Firebase."""

    class Meta:
        model = Usuario
        fields = ["fcm_token"]

    def validate_fcm_token(self, value):
        token = value.strip()
        if not token:
            raise serializers.ValidationError("El token FCM no puede estar vacío.")
        return token


class CambioRolSerializer(serializers.Serializer):
    """Serializer para cambiar el rol de un usuario."""

    rol = serializers.ChoiceField(choices=Usuario.Rol.choices)


class CommuSafeTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer JWT con datos del usuario embebidos en la respuesta."""

    username_field = Usuario.USERNAME_FIELD
    default_error_messages = {
        "no_active_account": "No existe una cuenta activa con las credenciales proporcionadas.",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["nombre"] = user.nombre
        token["apellido"] = user.apellido
        token["rol"] = user.rol
        token["unidad_residencial"] = user.unidad_residencial
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["usuario"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "nombre": self.user.nombre,
            "apellido": self.user.apellido,
            "nombre_completo": self.user.nombre_completo,
            "rol": self.user.rol,
            "unidad_residencial": self.user.unidad_residencial,
        }
        return data
