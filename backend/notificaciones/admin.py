"""Administración del módulo de notificaciones."""

from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """Configuración del modelo Notificacion."""

    list_display = ("titulo", "usuario", "tipo", "leida", "enviada_push", "creada_en")
    list_filter = ("tipo", "leida", "enviada_push", "creada_en")
    search_fields = ("titulo", "mensaje", "usuario__email")
    autocomplete_fields = ("usuario", "incidente")
    readonly_fields = ("creada_en", "leida_en")
