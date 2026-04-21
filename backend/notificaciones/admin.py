"""Administración del módulo de notificaciones."""

from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """Configuración del modelo Notificacion."""

    list_display = ("titulo", "destinatario", "tipo", "leida", "enviada_push", "fecha_envio")
    list_filter = ("tipo", "leida", "enviada_push", "fecha_envio")
    search_fields = ("titulo", "cuerpo", "destinatario__email")
    autocomplete_fields = ("destinatario", "incidente_relacionado")
    readonly_fields = ("fecha_envio",)
