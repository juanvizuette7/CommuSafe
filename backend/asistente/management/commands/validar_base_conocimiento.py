"""Valida la base local de conocimiento de CommuBot."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from asistente.local_knowledge import ALL_ROLES, FAQ_ENTRIES, knowledge_summary
from asistente.taxonomy import validate_taxonomy


SAFE_PENDING_TERMS = (
    "administracion",
    "validar",
    "validarse",
    "verificar",
    "no encuentro",
    "no emite",
    "deben validarse",
)


class Command(BaseCommand):
    help = "Valida diversidad, metadatos, vigencia y seguridad de la base local del asistente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--export-json",
            dest="export_json",
            help="Ruta opcional para exportar la base de conocimiento en JSON.",
        )

    def handle(self, *args, **options):
        errores = self._validar()
        resumen = knowledge_summary()
        resumen.update(
            {
                "intenciones_principales": len({entry.main_intent for entry in FAQ_ENTRIES}),
                "subintenciones_unicas": len({entry.intent for entry in FAQ_ENTRIES}),
                "preguntas_unicas": len({entry.question.lower().strip() for entry in FAQ_ENTRIES}),
                "ids_unicos": len({entry.id for entry in FAQ_ENTRIES}),
                "roles_validos": sorted(ALL_ROLES),
            }
        )

        export_path = options.get("export_json")
        if export_path:
            path = Path(export_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "resumen": resumen,
                        "entradas": [entry.to_dict() for entry in FAQ_ENTRIES],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            resumen["exportado_en"] = str(path)

        if errores:
            self.stdout.write(json.dumps({"resumen": resumen, "errores": errores}, ensure_ascii=False, indent=2))
            raise CommandError("La base de conocimiento no cumple los criterios de produccion.")

        self.stdout.write(
            json.dumps(
                {
                    "estado": "ok",
                    "resumen": resumen,
                    "criterios": [
                        "al_menos_100_preguntas_diferentes",
                        "ids_unicos",
                        "taxonomia_principal_sin_fragmentacion",
                        "subintenciones_unicas",
                        "categorias_multiples",
                        "roles_validos",
                        "metadatos_verificacion_y_vigencia",
                        "respuestas_pendientes_seguras",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    def _validar(self):
        errores = []
        ids = [entry.id for entry in FAQ_ENTRIES]
        subintents = [entry.intent for entry in FAQ_ENTRIES]
        questions = [entry.question.lower().strip() for entry in FAQ_ENTRIES]
        categories = {entry.category for entry in FAQ_ENTRIES}

        if len(FAQ_ENTRIES) < 100:
            errores.append("La base debe contener al menos 100 preguntas frecuentes.")
        if len(set(ids)) != len(ids):
            errores.append("Existen ids duplicados en la base de conocimiento.")
        if len(set(subintents)) != len(subintents):
            errores.append("Existen subintenciones FAQ duplicadas; revisa redundancia de conocimiento.")
        if len(set(questions)) != len(questions):
            errores.append("Existen preguntas principales duplicadas.")
        if len(categories) < 10:
            errores.append("La base debe mantener una cobertura amplia de categorias.")
        errores.extend(validate_taxonomy(set(ids)))

        for entry in FAQ_ENTRIES:
            if not entry.question.strip():
                errores.append(f"{entry.id}: pregunta vacia.")
            if not entry.answer.strip():
                errores.append(f"{entry.id}: respuesta vacia.")
            if len(entry.keywords) < 3:
                errores.append(f"{entry.id}: debe tener al menos 3 palabras clave.")
            if len(entry.variations) < 2:
                errores.append(f"{entry.id}: debe tener al menos 2 variaciones naturales.")
            if not set(entry.allowed_roles).issubset(set(ALL_ROLES)):
                errores.append(f"{entry.id}: contiene roles no permitidos.")
            if not entry.updated_at:
                errores.append(f"{entry.id}: falta fecha de actualizacion.")
            if not entry.valid_from:
                errores.append(f"{entry.id}: falta fecha de inicio de vigencia.")
            if entry.valid_until and not entry.is_active():
                errores.append(f"{entry.id}: entrada vencida y todavia registrada como utilizable.")
            if not entry.verified:
                texto = entry.answer.lower()
                if not any(term in texto for term in SAFE_PENDING_TERMS):
                    errores.append(f"{entry.id}: respuesta pendiente no remite a validacion segura.")

        return errores
