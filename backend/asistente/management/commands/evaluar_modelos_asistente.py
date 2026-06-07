"""Comando para entrenar, comparar y seleccionar modelos locales del asistente."""

import json

from django.core.management.base import BaseCommand

from asistente.model_selection import (
    export_model_selection_markdown,
    export_model_selection_report,
    train_compare_select_models,
)


class Command(BaseCommand):
    help = "Entrena, compara y selecciona modelos locales para clasificar intenciones de CommuBot."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Semilla deterministica del dataset.")
        parser.add_argument("--json", dest="json_path", help="Ruta opcional para exportar evidencia JSON.")
        parser.add_argument("--markdown", dest="markdown_path", help="Ruta opcional para exportar reporte Markdown.")
        parser.add_argument(
            "--full-output",
            action="store_true",
            help="Imprime todo el JSON en consola. Por defecto muestra resumen compacto.",
        )

    def handle(self, *args, **options):
        payload = train_compare_select_models(seed=options["seed"])
        export_model_selection_report(payload, options.get("json_path"))
        export_model_selection_markdown(payload, options.get("markdown_path"))
        if options["full_output"]:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        resumen = {
            "estado": "ok",
            "dataset": payload["resumen_dataset"],
            "modelo_seleccionado": payload["modelo_seleccionado"],
            "ranking": [
                {
                    "id": row["id"],
                    "validation_f1": row["validation_f1"],
                    "test_f1": row["test_f1"],
                    "challenge_f1": row["challenge_f1"],
                    "puntaje_generalizacion": row["puntaje_generalizacion"],
                }
                for row in payload["ranking"]
            ],
            "json_exportado": options.get("json_path") or "",
            "markdown_exportado": options.get("markdown_path") or "",
        }
        self.stdout.write(json.dumps(resumen, ensure_ascii=False, indent=2))
