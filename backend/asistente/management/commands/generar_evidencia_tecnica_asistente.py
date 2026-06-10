"""Genera evidencia academica reproducible del asistente hibrido."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from asistente.technical_evidence import export_evidence, generate_technical_evidence


class Command(BaseCommand):
    help = "Mide calidad, cobertura, tokens, consistencia y concurrencia del asistente hibrido."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--repeticiones", type=int, default=3)
        parser.add_argument("--solicitudes", type=int, default=600)
        parser.add_argument("--workers", type=int, default=20)
        parser.add_argument(
            "--json",
            dest="json_path",
            default="../docs/evidencias/asistente_evidencia_tecnica_2026.json",
        )
        parser.add_argument(
            "--markdown",
            dest="markdown_path",
            default="../docs/evidencias/asistente_evidencia_tecnica_2026.md",
        )
        parser.add_argument(
            "--produccion-json",
            dest="production_path",
            default="../docs/evidencias/asistente_metricas_produccion_2026-06-10.json",
            help="Snapshot operativo opcional, sin credenciales, para complementar el benchmark.",
        )
        parser.add_argument(
            "--pruebas-json",
            dest="tests_path",
            default="../docs/evidencias/asistente_validacion_pruebas_2026-06-10.json",
            help="Snapshot opcional de pruebas ejecutadas.",
        )

    def handle(self, *args, **options):
        payload = generate_technical_evidence(
            seed=options["seed"],
            repetitions=max(1, options["repeticiones"]),
            concurrency_requests=max(1, options["solicitudes"]),
            workers=max(1, options["workers"]),
        )
        production_path = Path(options["production_path"])
        if production_path.exists():
            production_snapshot = json.loads(production_path.read_text(encoding="utf-8"))
            if production_snapshot.get("alcance") == "usuarios_autenticados":
                payload["evidencia_produccion"] = production_snapshot
            else:
                payload["evidencia_produccion_descartada"] = {
                    "ruta": str(production_path),
                    "motivo": "El snapshot no declara alcance usuarios_autenticados y puede incluir ejecuciones tecnicas.",
                }
        tests_path = Path(options["tests_path"])
        if tests_path.exists():
            payload["evidencia_pruebas"] = json.loads(tests_path.read_text(encoding="utf-8"))
        export_evidence(payload, options["json_path"], options["markdown_path"])
        test = payload["evaluacion_test_independiente"]
        concurrency = payload["concurrencia"]
        summary = {
            "estado": "ok",
            "json": options["json_path"],
            "markdown": options["markdown_path"],
            "test": {
                "precision_micro": test["precision_micro"],
                "recall_macro": test["recall_macro"],
                "f1_macro": test["f1_macro"],
                "cobertura_local": test["cobertura_respuesta_local"],
                "tasa_candidata_gemini": test["tasa_candidata_gemini"],
                "consistencia": test["consistencia_repeticiones"],
                "tokens_ahorrados_estimados": test["tokens_externos_ahorrados_estimados"],
            },
            "concurrencia": {
                "solicitudes": concurrency["solicitudes"],
                "exitosas": concurrency["exitosas"],
                "errores": len(concurrency["errores"]),
                "contaminaciones_cache": concurrency["contaminaciones_cache"],
                "latencia_p95_ms": concurrency["latencia_ms"]["p95"],
            },
        }
        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
