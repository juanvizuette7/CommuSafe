"""Enrutamiento principal de CommuSafe Backend."""

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve as serve_media


FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#1A1A2E"/>
<path d="M32 9 50 17v13c0 11.8-7.2 20.2-18 25-10.8-4.8-18-13.2-18-25V17l18-8Z" fill="#0F3460"/>
<path d="M32 15 44 20v10c0 7.6-4.6 13.4-12 17-7.4-3.6-12-9.4-12-17V20l12-5Z" fill="#FFFFFF"/>
<path d="M28 33.6 23.8 29.4 20.8 32.4 28 39.6 43.2 24.4 40.2 21.4 28 33.6Z" fill="#16A34A"/>
</svg>"""
LOADER_IO_TOKEN = "loaderio-24994142aa27fcc0e43b4b8cd771e64d"


def favicon(_request):
    return HttpResponse(FAVICON_SVG, content_type="image/svg+xml")


def health_check(_request):
    return JsonResponse({"status": "ok", "servicio": "CommuSafe"})


def loaderio_verification(_request):
    return HttpResponse(LOADER_IO_TOKEN, content_type="text/plain")


urlpatterns = [
    path("favicon.ico", favicon, name="favicon"),
    path(f"{LOADER_IO_TOKEN}.txt", loaderio_verification, name="loaderio_verification_txt"),
    path(f"{LOADER_IO_TOKEN}.html", loaderio_verification, name="loaderio_verification_html"),
    path(f"{LOADER_IO_TOKEN}/", loaderio_verification, name="loaderio_verification_path"),
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
