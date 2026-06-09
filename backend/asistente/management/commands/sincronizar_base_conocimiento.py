"""Importa el catalogo inicial al repositorio administrable."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from asistente.local_knowledge import FAQ_ENTRIES
from asistente.models import EntradaConocimiento


class Command(BaseCommand):
    help = "Crea entradas administrables desde la base inicial sin sobrescribir cambios por defecto."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", required=True, help="Correo del administrador responsable.")
        parser.add_argument(
            "--actualizar",
            action="store_true",
            help="Actualiza tambien entradas existentes. Usar solo tras revisar los cambios.",
        )

    def handle(self, *args, **options):
        Usuario = get_user_model()
        try:
            responsable = Usuario.objects.get(email__iexact=options["usuario"])
        except Usuario.DoesNotExist as exc:
            raise CommandError("No existe un usuario con el correo indicado.") from exc

        if not (responsable.is_superuser or responsable.es_administrador):
            raise CommandError("El responsable debe tener rol administrador.")

        creadas = 0
        actualizadas = 0
        omitidas = 0
        for entrada in FAQ_ENTRIES:
            valores = self._valores_entrada(entrada, responsable)
            existente = EntradaConocimiento.objects.filter(codigo=entrada.id).first()
            if existente and not options["actualizar"]:
                omitidas += 1
                continue

            if existente:
                for campo, valor in valores.items():
                    setattr(existente, campo, valor)
                existente.actualizado_por = responsable
                existente.nota_cambio = "Sincronizada manualmente desde el catalogo inicial."
                existente.full_clean()
                existente.save()
                actualizadas += 1
                continue

            nueva = EntradaConocimiento(
                codigo=entrada.id,
                creado_por=responsable,
                actualizado_por=responsable,
                **valores,
            )
            nueva.full_clean()
            nueva.save()
            creadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Base sincronizada. Creadas: {creadas}. Actualizadas: {actualizadas}. "
                f"Omitidas sin sobrescribir: {omitidas}."
            )
        )

    @staticmethod
    def _valores_entrada(entrada, responsable):
        aprobada = bool(entrada.verified)
        return {
            "pregunta": entrada.question,
            "respuesta": entrada.answer,
            "categoria": entrada.category,
            "intencion_principal": entrada.main_intent,
            "subintencion": entrada.intent,
            "palabras_clave": list(entrada.keywords),
            "variaciones": list(entrada.variations),
            "roles_permitidos": list(entrada.allowed_roles),
            "estado": (
                EntradaConocimiento.Estado.APROBADA
                if aprobada
                else EntradaConocimiento.Estado.EN_REVISION
            ),
            "vigente_desde": Command._fecha_segura(entrada.valid_from),
            "vigente_hasta": Command._fecha_segura(entrada.valid_until, requerida=False),
            "fuente": entrada.source,
            "nota_cambio": "Importada desde el catalogo inicial verificado.",
            "aprobado_por": responsable if aprobada else None,
            "fecha_aprobacion": timezone.now() if aprobada else None,
        }

    @staticmethod
    def _fecha_segura(valor, requerida=True):
        if valor:
            try:
                return date.fromisoformat(valor)
            except ValueError:
                pass
        return timezone.localdate() if requerida else None
