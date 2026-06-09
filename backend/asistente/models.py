"""Modelos persistentes del asistente virtual."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


def roles_conocimiento_default():
    return ["RESIDENTE", "VIGILANTE", "ADMINISTRADOR"]


def lista_vacia():
    return []


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


class EntradaConocimiento(models.Model):
    """Pregunta y respuesta administrable publicada solo tras aprobacion."""

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        EN_REVISION = "EN_REVISION", "En revision"
        APROBADA = "APROBADA", "Aprobada"
        INACTIVA = "INACTIVA", "Inactiva"
        RECHAZADA = "RECHAZADA", "Rechazada"

    CAMPOS_VERSIONADOS = (
        "codigo",
        "pregunta",
        "respuesta",
        "categoria",
        "intencion_principal",
        "subintencion",
        "palabras_clave",
        "variaciones",
        "roles_permitidos",
        "estado",
        "vigente_desde",
        "vigente_hasta",
        "fuente",
        "nota_cambio",
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.SlugField(max_length=120, unique=True)
    pregunta = models.CharField(max_length=300)
    respuesta = models.TextField()
    categoria = models.CharField(max_length=80, db_index=True)
    intencion_principal = models.CharField(max_length=120, db_index=True)
    subintencion = models.CharField(max_length=120, blank=True)
    palabras_clave = models.JSONField(default=lista_vacia, blank=True)
    variaciones = models.JSONField(default=lista_vacia, blank=True)
    roles_permitidos = models.JSONField(default=roles_conocimiento_default)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        db_index=True,
    )
    vigente_desde = models.DateField(default=timezone.localdate)
    vigente_hasta = models.DateField(null=True, blank=True)
    fuente = models.CharField(max_length=240, blank=True)
    nota_cambio = models.CharField(max_length=300, blank=True)
    version = models.PositiveIntegerField(default=1, editable=False)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="conocimiento_creado",
        null=True,
        blank=True,
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="conocimiento_actualizado",
        null=True,
        blank=True,
    )
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="conocimiento_aprobado",
        null=True,
        blank=True,
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = "Entrada de conocimiento"
        verbose_name_plural = "Base de conocimiento"
        ordering = ("categoria", "pregunta")
        indexes = [
            models.Index(fields=["estado", "fecha_actualizacion"]),
            models.Index(fields=["categoria", "estado"]),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.pregunta}"

    def clean(self):
        roles_validos = {"RESIDENTE", "VIGILANTE", "ADMINISTRADOR"}
        roles = self.roles_permitidos or []
        if not isinstance(roles, list) or not roles or not set(roles).issubset(roles_validos):
            raise ValidationError({"roles_permitidos": "Selecciona uno o mas roles validos."})
        if (
            not isinstance(self.palabras_clave, list)
            or len(self.palabras_clave) < 3
            or any(not isinstance(valor, str) or not valor.strip() for valor in self.palabras_clave)
        ):
            raise ValidationError({"palabras_clave": "Registra al menos tres palabras clave."})
        if (
            not isinstance(self.variaciones, list)
            or len(self.variaciones) < 2
            or any(not isinstance(valor, str) or not valor.strip() for valor in self.variaciones)
        ):
            raise ValidationError({"variaciones": "Registra al menos dos formas alternativas de preguntar."})
        if self.vigente_hasta and self.vigente_hasta < self.vigente_desde:
            raise ValidationError({"vigente_hasta": "La fecha final no puede ser anterior a la fecha inicial."})
        if self.estado == self.Estado.APROBADA and not self.aprobado_por:
            raise ValidationError({"estado": "Una entrada aprobada debe registrar quien la aprobo."})

    def save(self, *args, **kwargs):
        if not self.pk:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            anterior = (
                type(self)
                .objects.select_for_update()
                .filter(pk=self.pk)
                .values(*self.CAMPOS_VERSIONADOS, "version")
                .first()
            )
            if anterior and anterior["codigo"] != self.codigo:
                raise ValidationError({"codigo": "El codigo de una entrada no puede modificarse."})
            if anterior and any(anterior[campo] != getattr(self, campo) for campo in self.CAMPOS_VERSIONADOS):
                self.version = anterior["version"] + 1
                if kwargs.get("update_fields"):
                    kwargs["update_fields"] = set(kwargs["update_fields"]) | {"version"}
            return super().save(*args, **kwargs)

    def esta_publicable(self, fecha=None):
        fecha = fecha or timezone.localdate()
        if self.estado != self.Estado.APROBADA:
            return False
        if self.vigente_desde and self.vigente_desde > fecha:
            return False
        return not self.vigente_hasta or self.vigente_hasta >= fecha

    def snapshot(self):
        return {
            campo: getattr(self, campo).isoformat()
            if hasattr(getattr(self, campo), "isoformat")
            else getattr(self, campo)
            for campo in self.CAMPOS_VERSIONADOS
        }


class VersionEntradaConocimiento(models.Model):
    """Snapshot inmutable de cada version de una entrada."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entrada = models.ForeignKey(
        EntradaConocimiento,
        on_delete=models.CASCADE,
        related_name="historial_versiones",
    )
    version = models.PositiveIntegerField()
    datos = models.JSONField(default=dict)
    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="versiones_conocimiento",
        null=True,
        blank=True,
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Version de conocimiento"
        verbose_name_plural = "Versiones de conocimiento"
        ordering = ("-fecha_cambio",)
        constraints = [
            models.UniqueConstraint(fields=["entrada", "version"], name="uq_conocimiento_entrada_version"),
        ]

    def __str__(self):
        return f"{self.entrada.codigo} v{self.version}"


class ConsultaSinRespuesta(models.Model):
    """Consulta agrupada que aun no tiene conocimiento local aprobado suficiente."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_REVISION = "EN_REVISION", "En revision"
        CONVERTIDA = "CONVERTIDA", "Convertida en conocimiento"
        DESCARTADA = "DESCARTADA", "Descartada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    huella = models.CharField(max_length=64)
    rol = models.CharField(max_length=20, db_index=True)
    consulta_muestra = models.TextField()
    consulta_normalizada = models.TextField()
    cantidad = models.PositiveIntegerField(default=1, db_index=True)
    confianza_maxima = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    intencion_sugerida = models.CharField(max_length=120, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True)
    entrada_generada = models.ForeignKey(
        EntradaConocimiento,
        on_delete=models.SET_NULL,
        related_name="consultas_origen",
        null=True,
        blank=True,
    )
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="consultas_conocimiento_revisadas",
        null=True,
        blank=True,
    )
    fecha_primera_consulta = models.DateTimeField(auto_now_add=True)
    fecha_ultima_consulta = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = "Consulta sin respuesta"
        verbose_name_plural = "Consultas sin respuesta"
        ordering = ("-cantidad", "-fecha_ultima_consulta")
        constraints = [
            models.UniqueConstraint(fields=["huella", "rol"], name="uq_consulta_sin_respuesta_huella_rol"),
        ]
        indexes = [
            models.Index(fields=["estado", "cantidad"]),
        ]

    def __str__(self):
        return f"{self.cantidad}x - {self.consulta_muestra[:80]}"
