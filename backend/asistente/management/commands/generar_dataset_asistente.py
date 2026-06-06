"""Genera y valida el dataset profesional de entrenamiento del asistente."""

import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from asistente.training_dataset import (
    build_professional_dataset,
    dataset_summary,
    validate_professional_dataset,
)


class Command(BaseCommand):
    help = "Construye, valida y exporta el dataset train/validation/test de CommuBot."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--json", dest="json_path", help="Ruta para exportar JSON.")
        parser.add_argument("--csv-dir", dest="csv_dir", help="Directorio para exportar CSV por split.")

    def handle(self, *args, **options):
        splits = build_professional_dataset(seed=options["seed"])
        errors = validate_professional_dataset(splits)
        summary = dataset_summary(splits)

        if options.get("json_path"):
            path = Path(options["json_path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "resumen": summary,
                        "splits": {
                            split: [example.to_dict() for example in examples]
                            for split, examples in splits.items()
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            summary["json_exportado"] = str(path)

        if options.get("csv_dir"):
            directory = Path(options["csv_dir"])
            directory.mkdir(parents=True, exist_ok=True)
            for split, examples in splits.items():
                path = directory / f"{split}.csv"
                with path.open("w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.DictWriter(
                        csv_file,
                        fieldnames=[
                            "text",
                            "intent",
                            "subintent",
                            "category",
                            "role",
                            "entry_id",
                            "style",
                            "split",
                            "verified",
                            "requires_admin_validation",
                        ],
                    )
                    writer.writeheader()
                    writer.writerows(example.to_dict() for example in examples)
            summary["csv_exportado"] = str(directory)

        payload = {"estado": "ok" if not errors else "error", "resumen": summary, "errores": errors}
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))

        if errors:
            raise CommandError("El dataset del asistente contiene errores de coherencia.")
