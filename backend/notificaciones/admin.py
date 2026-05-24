"""Administración del módulo de notificaciones."""

from django.contrib import admin

from .models import AvisoProgramado, Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """Configuración del modelo Notificacion."""

    list_display = ("titulo", "destinatario", "tipo", "leida", "enviada_push", "fecha_envio")
    list_filter = ("tipo", "leida", "enviada_push", "fecha_envio")
    search_fields = ("titulo", "cuerpo", "destinatario__email")
    autocomplete_fields = ("destinatario", "incidente_relacionado")
    readonly_fields = ("fecha_envio",)


@admin.register(AvisoProgramado)
class AvisoProgramadoAdmin(admin.ModelAdmin):
    """Configuracion de avisos recurrentes desde el admin de Django."""

    list_display = (
        "titulo",
        "tipo",
        "audiencia",
        "dias_semana_display",
        "fecha_inicio",
        "fecha_fin",
        "ultimo_envio",
        "activo",
    )
    list_filter = ("tipo", "audiencia", "activo", "fecha_inicio")
    search_fields = ("titulo", "cuerpo", "creado_por__email")
    autocomplete_fields = ("creado_por", "destinatarios")
    filter_horizontal = ("destinatarios",)
    readonly_fields = ("creado_en", "actualizado_en", "ultimo_envio")
