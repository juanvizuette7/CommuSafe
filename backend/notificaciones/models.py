"""Modelos del módulo de notificaciones."""

import uuid

from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    """Mensaje interno generado por el sistema para un usuario."""

    class Tipo(models.TextChoices):
        INCIDENTE = "INCIDENTE", "Incidente"
        SISTEMA = "SISTEMA", "Sistema"
        RECORDATORIO = "RECORDATORIO", "Recordatorio"
        ALERTA = "ALERTA", "Alerta"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )
    incidente = models.ForeignKey(
        "incidentes.Incidente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificaciones",
    )
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.INCIDENTE)
    leida = models.BooleanField(default=False)
    enviada_push = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)
    leida_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ("-creada_en",)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.email}"
