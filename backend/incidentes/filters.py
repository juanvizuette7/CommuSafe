"""Filtros personalizados para el módulo de incidentes."""

from rest_framework.filters import OrderingFilter


class IncidenteOrderingFilter(OrderingFilter):
    """Mapea el orden por prioridad hacia un campo anotado numérico."""

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ordering

        ordering_mapeado = []
        for campo in ordering:
            descendente = campo.startswith("-")
            nombre = campo[1:] if descendente else campo
            nombre = "prioridad_orden" if nombre == "prioridad" else nombre
            ordering_mapeado.append(f"-{nombre}" if descendente else nombre)
        return ordering_mapeado
