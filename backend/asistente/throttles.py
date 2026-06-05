"""Limites de uso especificos para el asistente virtual."""

from rest_framework.throttling import UserRateThrottle


class AsistenteChatThrottle(UserRateThrottle):
    """Limita mensajes que pueden consumir procesamiento local o IA generativa."""

    scope = "asistente_chat"
    rate = "30/min"


class AsistenteLecturaThrottle(UserRateThrottle):
    """Limita consultas de historial y health sin afectar el uso normal."""

    scope = "asistente_lectura"
    rate = "120/min"
