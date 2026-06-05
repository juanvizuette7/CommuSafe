"""Modelos persistentes del asistente virtual."""

import uuid

from django.conf import settings
from django.db import models


class ConversacionAsistente(models.Model):
    """Chat independiente entre un usuario y CommuBot."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversaciones_asistente",
    )
    titulo = models.CharField(max_length=90, default="Nueva conversación")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conversación del asistente"
        verbose_name_plural = "Conversaciones del asistente"
        ordering = ("-fecha_actualizacion",)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.email}"


class MensajeAsistente(models.Model):
    """Mensaje persistente dentro de una conversación del asistente."""

    class Rol(models.TextChoices):
        USUARIO = "USUARIO", "Usuario"
        ASISTENTE = "ASISTENTE", "Asistente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversacion = models.ForeignKey(
        ConversacionAsistente,
        on_delete=models.CASCADE,
        related_name="mensajes",
    )
    rol = models.CharField(max_length=12, choices=Rol.choices)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje del asistente"
        verbose_name_plural = "Mensajes del asistente"
        ordering = ("fecha_creacion",)

    def __str__(self):
        return f"{self.get_rol_display()} - {self.conversacion.titulo}"


class AsistenteRespuestaLog(models.Model):
    """Trazabilidad tecnica de cada respuesta generada por CommuBot."""

    class Modo(models.TextChoices):
        LOCAL = "local", "Local"
        SEMANTICA = "semantica", "Semantica"
        ACLARACION = "aclaracion", "Aclaracion"
        IA = "ia", "IA generativa"
        SEGURA = "segura", "Respuesta segura"
        FALLBACK = "fallback", "Fallback"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="logs_asistente",
        null=True,
        blank=True,
    )
    conversacion = models.ForeignKey(
        ConversacionAsistente,
        on_delete=models.SET_NULL,
        related_name="logs_respuesta",
        null=True,
        blank=True,
    )
    mensaje = models.TextField()
    modo = models.CharField(max_length=20, choices=Modo.choices, db_index=True)
    proveedor = models.CharField(max_length=40, blank=True)
    modelo = models.CharField(max_length=80, blank=True)
    intencion = models.CharField(max_length=120, blank=True, db_index=True)
    categoria = models.CharField(max_length=80, blank=True)
    metodo = models.CharField(max_length=80, blank=True)
    confianza = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    latencia_ms = models.PositiveIntegerField(default=0)
    tokens_entrada = models.PositiveIntegerField(null=True, blank=True)
    tokens_salida = models.PositiveIntegerField(null=True, blank=True)
    requiere_validacion = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de respuesta del asistente"
        verbose_name_plural = "Logs de respuestas del asistente"
        ordering = ("-fecha_creacion",)
        indexes = [
            models.Index(fields=["modo", "fecha_creacion"]),
            models.Index(fields=["intencion", "fecha_creacion"]),
        ]

    def __str__(self):
        return f"{self.modo} - {self.intencion or 'sin intencion'}"
