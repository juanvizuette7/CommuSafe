"""Vistas base del panel web."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class InicioPanelView(LoginRequiredMixin, TemplateView):
    """Pantalla inicial del panel web."""

    template_name = "panel_web/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Panel de control CommuSafe"
        context["usuario"] = self.request.user
        return context
