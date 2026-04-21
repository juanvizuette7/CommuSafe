"""Etiquetas y filtros auxiliares para el panel web."""

from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """Construye una query string preservando los parámetros actuales."""

    request = context["request"]
    query = request.GET.copy()
    for clave, valor in kwargs.items():
        if valor in (None, "", False):
            query.pop(clave, None)
        else:
            query[clave] = valor
    if "page" not in kwargs:
        query.pop("page", None)
    encoded = query.urlencode()
    return f"?{encoded}" if encoded else ""
