"""Procesa reglas activas de avisos recurrentes."""

from django.core.management.base import BaseCommand

from notificaciones.services import procesar_avisos_programados


class Command(BaseCommand):
    help = "Envia los avisos programados pendientes para la fecha actual."

    def handle(self, *args, **options):
        resultado = procesar_avisos_programados()
        self.stdout.write(
            self.style.SUCCESS(
                "Avisos programados procesados: "
                f"{resultado['avisos_procesados']} regla(s), "
                f"{resultado['notificaciones_creadas']} notificacion(es)."
            )
        )
