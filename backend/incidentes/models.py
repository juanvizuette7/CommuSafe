"""Modelos del dominio de incidentes."""

import os
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def ruta_evidencia_incidente(instance, filename):
    """Genera una ruta organizada por año y mes para cada evidencia."""

    extension = os.path.splitext(filename)[1].lower() or ".jpg"
    fecha = timezone.now()
    nombre = f"{uuid.uuid4()}{extension}"
    return f"incidentes/evidencias/{fecha:%Y}/{fecha:%m}/{nombre}"


class Incidente(models.Model):
    """Representa un incidente reportado dentro del conjunto residencial."""

    class Categoria(models.TextChoices):
        SEGURIDAD = "SEGURIDAD", "Seguridad"
        CONVIVENCIA = "CONVIVENCIA", "Convivencia"
        INFRAESTRUCTURA = "INFRAESTRUCTURA", "Infraestructura"
        EMERGENCIA = "EMERGENCIA", "Emergencia"

    class Prioridad(models.TextChoices):
        ALTA = "ALTA", "Alta"
        MEDIA = "MEDIA", "Media"
        BAJA = "BAJA", "Baja"

    class Estado(models.TextChoices):
        REGISTRADO = "REGISTRADO", "Registrado"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        RESUELTO = "RESUELTO", "Resuelto"
        CERRADO = "CERRADO", "Cerrado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, editable=False)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.REGISTRADO)
    ubicacion_referencia = models.CharField(max_length=255, blank=True)
    reportado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="incidentes_reportados",
    )
    atendido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="incidentes_atendidos",
        null=True,
        blank=True,
    )
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    observaciones_cierre = models.TextField(blank=True)

    class Meta:
        verbose_name = "Incidente"
        verbose_name_plural = "Incidentes"
        ordering = ("-fecha_reporte",)

    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"

    def calcular_prioridad(self):
        if self.categoria in {self.Categoria.EMERGENCIA, self.Categoria.SEGURIDAD}:
            return self.Prioridad.ALTA
        if self.categoria == self.Categoria.CONVIVENCIA:
            return self.Prioridad.MEDIA
        return self.Prioridad.BAJA

    def save(self, *args, **kwargs):
        self.prioridad = self.calcular_prioridad()
        super().save(*args, **kwargs)


class EvidenciaIncidente(models.Model):
    """Imágenes asociadas a un incidente."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incidente = models.ForeignKey(
        Incidente,
        on_delete=models.CASCADE,
        related_name="evidencias",
    )
    imagen = models.ImageField(upload_to=ruta_evidencia_incidente)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evidencia de incidente"
        verbose_name_plural = "Evidencias de incidentes"
        ordering = ("-fecha_subida",)

    def __str__(self):
        return f"Evidencia de {self.incidente.titulo}"


class HistorialEstado(models.Model):
    """Registro inmutable de cambios de estado del incidente."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incidente = models.ForeignKey(
        Incidente,
        on_delete=models.CASCADE,
        related_name="historial",
    )
    estado_anterior = models.CharField(
        max_length=20,
        choices=Incidente.Estado.choices,
        blank=True,
        default="",
    )
    estado_nuevo = models.CharField(max_length=20, choices=Incidente.Estado.choices)
    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cambios_estado_incidentes",
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True)

    class Meta:
        verbose_name = "Historial de estado"
        verbose_name_plural = "Historiales de estado"
        ordering = ("-fecha_cambio",)

    def __str__(self):
        return f"{self.incidente.titulo}: {self.estado_anterior or 'SIN ESTADO'} -> {self.estado_nuevo}"
