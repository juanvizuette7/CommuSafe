"""Administración del módulo de asistente virtual."""

from django.contrib import admin

from .models import AsistenteRespuestaLog, ConversacionAsistente, MensajeAsistente


class MensajeAsistenteInline(admin.TabularInline):
    model = MensajeAsistente
    extra = 0
    readonly_fields = ("rol", "contenido", "fecha_creacion")
    can_delete = False


@admin.register(ConversacionAsistente)
class ConversacionAsistenteAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "fecha_creacion", "fecha_actualizacion")
    list_filter = ("fecha_creacion", "fecha_actualizacion")
    search_fields = ("titulo", "usuario__email", "usuario__nombre", "usuario__apellido")
    autocomplete_fields = ("usuario",)
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    inlines = (MensajeAsistenteInline,)


@admin.register(MensajeAsistente)
class MensajeAsistenteAdmin(admin.ModelAdmin):
    list_display = ("conversacion", "rol", "fecha_creacion")
    list_filter = ("rol", "fecha_creacion")
    search_fields = ("contenido", "conversacion__titulo", "conversacion__usuario__email")
    autocomplete_fields = ("conversacion",)
    readonly_fields = ("fecha_creacion",)


@admin.register(AsistenteRespuestaLog)
class AsistenteRespuestaLogAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_creacion",
        "usuario",
        "modo",
        "proveedor",
        "intencion",
        "confianza",
        "latencia_ms",
        "requiere_validacion",
    )
    list_filter = ("modo", "proveedor", "categoria", "requiere_validacion", "fecha_creacion")
    search_fields = ("mensaje", "intencion", "usuario__email", "usuario__nombre", "usuario__apellido")
    autocomplete_fields = ("usuario", "conversacion")
    readonly_fields = (
        "usuario",
        "conversacion",
        "mensaje",
        "modo",
        "proveedor",
        "modelo",
        "intencion",
        "categoria",
        "metodo",
        "confianza",
        "latencia_ms",
        "tokens_entrada",
        "tokens_salida",
        "requiere_validacion",
        "metadata",
        "fecha_creacion",
    )
