"""Modelos de la app de usuarios."""

import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def generar_token_reset_password():
    """Genera un token criptograficamente seguro para recuperacion de contrasena."""

    return secrets.token_urlsafe(48)


def expira_token_reset_password():
    """Define la expiracion por defecto de un token de recuperacion."""

    return timezone.now() + timedelta(hours=1)


class UsuarioManager(BaseUserManager):
    """Manager del usuario personalizado."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        if not password:
            raise ValueError("La contraseña es obligatoria.")

        email = self.normalize_email(email).lower()
        extra_fields.setdefault("rol", Usuario.Rol.RESIDENTE)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.full_clean()
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("rol", Usuario.Rol.ADMINISTRADOR)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("activo", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Modelo principal de usuarios del sistema."""

    class Rol(models.TextChoices):
        RESIDENTE = "RESIDENTE", "Residente"
        VIGILANTE = "VIGILANTE", "Vigilante"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=120)
    apellido = models.CharField(max_length=120)
    unidad_residencial = models.CharField(max_length=120, blank=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.RESIDENTE)
    telefono = models.CharField(max_length=30, blank=True)
    fcm_token = models.TextField(blank=True)
    foto_perfil = models.ImageField(upload_to="usuarios/fotos/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ("-fecha_registro",)

    def __str__(self):
        return f"{self.nombre_completo} <{self.email}>"

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        self.nombre = self.nombre.strip()
        self.apellido = self.apellido.strip()
        self.unidad_residencial = self.unidad_residencial.strip()
        self.telefono = self.telefono.strip()
        if self.rol == self.Rol.RESIDENTE and not self.unidad_residencial:
            raise ValidationError(
                {"unidad_residencial": "La unidad residencial es obligatoria para residentes."}
            )

    @property
    def is_active(self):
        return self.activo

    @is_active.setter
    def is_active(self, value):
        self.activo = value

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_vigilante(self):
        return self.rol == self.Rol.VIGILANTE

    @property
    def es_residente(self):
        return self.rol == self.Rol.RESIDENTE

    def get_full_name(self):
        return self.nombre_completo

    def get_short_name(self):
        return self.nombre


class PasswordResetToken(models.Model):
    """Token de un solo uso para recuperar la contrasena de una cuenta."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tokens_reset_password",
    )
    token = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        default=generar_token_reset_password,
        editable=False,
    )
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    expira = models.DateTimeField(default=expira_token_reset_password)

    class Meta:
        verbose_name = "Token de recuperacion de contrasena"
        verbose_name_plural = "Tokens de recuperacion de contrasena"
        ordering = ("-creado",)

    def __str__(self):
        return f"Reset de {self.usuario.email} - {'usado' if self.usado else 'activo'}"

    @property
    def esta_vigente(self):
        return not self.usado and self.expira > timezone.now() and self.usuario.activo
