"""Configuración de producción para CommuSafe Backend."""

from decouple import Csv, config

from .settings import *  # noqa: F401,F403


DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="5432"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "CONN_MAX_AGE": 600,
    }
}

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=cast_bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
_csrf_trusted_origins = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
CSRF_TRUSTED_ORIGINS = [origin for origin in _csrf_trusted_origins if origin]
