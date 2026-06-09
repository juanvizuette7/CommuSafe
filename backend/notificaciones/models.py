"""Modelos del módulo de notificaciones."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


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
    deduplicacion_clave = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ("-fecha_envio",)

    def __str__(self):
        return f"{self.titulo} - {self.destinatario.email}"


class AvisoProgramado(models.Model):
    """Regla de repeticion para avisos comunitarios recurrentes."""

    DIAS_SEMANA = (
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miercoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sabado"),
        (6, "Domingo"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=150)
    cuerpo = models.TextField()
    tipo = models.CharField(max_length=20, choices=Notificacion.Tipo.choices)
    audiencia = models.CharField(max_length=20)
    destinatarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="avisos_programados_asignados",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="avisos_programados_creados",
    )
    dias_semana = models.CharField(max_length=20)
    fecha_inicio = models.DateField(default=timezone.localdate)
    fecha_fin = models.DateField(null=True, blank=True)
    ultimo_envio = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Aviso programado"
        verbose_name_plural = "Avisos programados"
        ordering = ("-activo", "titulo")

    def __str__(self):
        return f"{self.titulo} ({self.dias_semana_display})"

    @property
    def dias_semana_lista(self):
        if not self.dias_semana:
            return []
        return [int(dia) for dia in self.dias_semana.split(",") if dia.strip().isdigit()]

    @property
    def dias_semana_display(self):
        nombres = dict(self.DIAS_SEMANA)
        return ", ".join(nombres[dia] for dia in self.dias_semana_lista if dia in nombres)

    def debe_enviarse(self, fecha=None):
        fecha = fecha or timezone.localdate()
        if not self.activo:
            return False
        if fecha < self.fecha_inicio:
            return False
        if self.fecha_fin and fecha > self.fecha_fin:
            return False
        if self.ultimo_envio == fecha:
            return False
        return fecha.weekday() in self.dias_semana_lista
