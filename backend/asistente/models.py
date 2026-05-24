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
