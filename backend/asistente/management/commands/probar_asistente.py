"""Comando para validar credenciales reales del asistente IA."""

from django.core.management.base import BaseCommand, CommandError

from asistente.views import generar_respuesta_asistente


class Command(BaseCommand):
    help = "Prueba el asistente virtual desde consola usando el proveedor configurado."

    def add_arguments(self, parser):
        parser.add_argument(
            "mensaje",
            nargs="+",
            help="Mensaje que se enviara al asistente virtual.",
        )

    def handle(self, *args, **options):
        mensaje = " ".join(options["mensaje"]).strip()
        if not mensaje:
            raise CommandError("Debes escribir un mensaje para probar el asistente.")

        resultado = generar_respuesta_asistente(mensaje)
        self.stdout.write(self.style.SUCCESS(f"Proveedor: {resultado['proveedor']}"))
        if resultado.get("modelo_usado"):
            self.stdout.write(self.style.SUCCESS(f"Modelo: {resultado['modelo_usado']}"))
        self.stdout.write("")
        self.stdout.write(resultado["respuesta"])
