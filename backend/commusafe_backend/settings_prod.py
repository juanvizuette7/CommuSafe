"""Configuracion de produccion para CommuSafe Backend."""

import os

import dj_database_url
from decouple import Csv, config

from .settings import *  # noqa: F401,F403


DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default=".onrender.com", cast=Csv())

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        conn_max_age=600,
        ssl_require=True,
    )
}

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000

_csrf_trusted_origins = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://*.onrender.com",
    cast=Csv(),
)
CSRF_TRUSTED_ORIGINS = [origin for origin in _csrf_trusted_origins if origin]
