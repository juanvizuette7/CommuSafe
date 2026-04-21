"""Modelos del módulo de notificaciones."""

import uuid

from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    """Mensaje interno generado por el sistema para un usuario."""

    class Tipo(models.TextChoices):
        INCIDENTE_NUEVO = "INCIDENTE_NUEVO", "Incidente nuevo"
        CAMBIO_ESTADO = "CAMBIO_ESTADO", "Cambio de estado"
        AVISO_ADMIN = "AVISO_ADMIN", "Aviso administrativo"
        EMERGENCIA = "EMERGENCIA", "Emergencia"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )
    titulo = models.CharField(max_length=150)
    cuerpo = models.TextField()
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    leida = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    incidente_relacionado = models.ForeignKey(
        "incidentes.Incidente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificaciones",
    )
    enviada_push = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ("-fecha_envio",)

    def __str__(self):
        return f"{self.titulo} - {self.destinatario.email}"
