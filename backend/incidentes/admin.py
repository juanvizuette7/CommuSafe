"""Administración del módulo de incidentes."""

from django.contrib import admin

from .models import EvidenciaIncidente, HistorialEstado, Incidente, IncidenteEliminado


class EvidenciaIncidenteInline(admin.TabularInline):
    """Inline de evidencias para el incidente."""

    model = EvidenciaIncidente
    extra = 0
    fields = ("imagen", "descripcion", "fecha_subida")
    readonly_fields = ("fecha_subida",)


class HistorialEstadoInline(admin.TabularInline):
    """Inline de historial de cambios."""

    model = HistorialEstado
    extra = 0
    fields = ("estado_anterior", "estado_nuevo", "cambiado_por", "fecha_cambio", "comentario")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    """Configuración del modelo Incidente en el admin."""

    list_display = (
        "titulo",
        "categoria",
        "prioridad",
        "estado",
        "reportado_por",
        "atendido_por",
        "fecha_reporte",
    )
    list_filter = ("categoria", "prioridad", "estado", "fecha_reporte")
    search_fields = ("titulo", "descripcion", "ubicacion_referencia", "reportado_por__email")
    autocomplete_fields = ("reportado_por", "atendido_por")
    readonly_fields = ("prioridad", "fecha_reporte", "fecha_actualizacion", "fecha_cierre")
    inlines = [EvidenciaIncidenteInline, HistorialEstadoInline]


@admin.register(EvidenciaIncidente)
class EvidenciaIncidenteAdmin(admin.ModelAdmin):
    """Configuración del modelo EvidenciaIncidente."""

    list_display = ("incidente", "descripcion", "fecha_subida")
    search_fields = ("incidente__titulo", "descripcion")
    autocomplete_fields = ("incidente",)
    readonly_fields = ("fecha_subida",)


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    """Configuración del modelo HistorialEstado."""

    list_display = ("incidente", "estado_anterior", "estado_nuevo", "cambiado_por", "fecha_cambio")
    list_filter = ("estado_anterior", "estado_nuevo", "fecha_cambio")
    search_fields = ("incidente__titulo", "comentario", "cambiado_por__email")
    autocomplete_fields = ("incidente", "cambiado_por")
    readonly_fields = ("fecha_cambio",)


@admin.register(IncidenteEliminado)
class IncidenteEliminadoAdmin(admin.ModelAdmin):
    """Auditoria de incidentes eliminados fisicamente."""

    list_display = ("titulo", "incidente_id", "eliminado_por", "fecha_eliminacion")
    list_filter = ("fecha_eliminacion",)
    search_fields = ("titulo", "motivo", "eliminado_por__email")
    autocomplete_fields = ("eliminado_por",)
    readonly_fields = ("incidente_id", "titulo", "eliminado_por", "fecha_eliminacion", "motivo")
