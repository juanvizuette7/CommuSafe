"""Enrutamiento principal de CommuSafe Backend."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_media


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("usuarios.urls")),
    path("api/incidentes/", include("incidentes.urls")),
    path("api/notificaciones/", include("notificaciones.urls")),
    path("api/asistente/", include("asistente.urls")),
    path(
        "loaderio-20dfbcf3e86f90389ce99fdc75050188.txt",
        serve_media,
        {
            "path": "loaderio-20dfbcf3e86f90389ce99fdc75050188.txt",
            "document_root": settings.PUBLIC_ROOT,
            "show_indexes": False,
        },
    ),
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
