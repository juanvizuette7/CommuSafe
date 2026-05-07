"""Enrutamiento principal de CommuSafe Backend."""

from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve as serve_media


def health_check(_request):
    return JsonResponse({"status": "ok", "servicio": "CommuSafe"})


urlpatterns = [
    path("health/", health_check, name="health"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("usuarios.urls")),
    path("api/incidentes/", include("incidentes.urls")),
    path("api/notificaciones/", include("notificaciones.urls")),
    path("api/asistente/", include("asistente.urls")),
    path("", include("panel_web.urls")),
]

if settings.DEBUG or getattr(settings, "SERVE_MEDIA_FILES", False):
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve_media,
            {"document_root": settings.MEDIA_ROOT, "show_indexes": False},
        )
    ]
