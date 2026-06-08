"""Prueba de carga y resiliencia del motor local del asistente."""

from __future__ import annotations

import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from asistente.local_engine import resolve_local_answer


PREGUNTAS_REALISTAS = [
    ("RESIDENTE", "Como reporto un incidente?"),
    ("RESIDENTE", "No puedo entrar a mi cuenta"),
    ("RESIDENTE", "Que hago si hay ruido de noche?"),
    ("RESIDENTE", "Donde veo las notificaciones?"),
    ("RESIDENTE", "Como hago seguimiento a un reporte?"),
    ("RESIDENTE", "Que hago si una mascota causa molestias?"),
    ("RESIDENTE", "Como reporto un dano en zona comun?"),
    ("RESIDENTE", "Que hago si un vehiculo bloquea el paso?"),
    ("VIGILANTE", "Como atiendo un incidente en proceso?"),
    ("ADMINISTRADOR", "Como publico un aviso para residentes?"),
    ("RESIDENTE", "procedimiento biometrico de porteria para QR temporal"),
    ("RESIDENTE", "quien gano el partido de futbol ayer"),
]


def _percentil(valores, percentil):
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    indice = int(round((len(ordenados) - 1) * (percentil / 100)))
    return round(ordenados[indice], 3)


class Command(BaseCommand):
    help = "Ejecuta una prueba concurrente local del asistente sin usar IA externa."

    def add_arguments(self, parser):
        parser.add_argument("--requests", type=int, default=80, help="Cantidad de solicitudes simuladas.")
        parser.add_argument("--workers", type=int, default=8, help="Cantidad de hilos concurrentes.")

    def handle(self, *args, **options):
        total = max(1, int(options["requests"]))
        workers = max(1, int(options["workers"]))
        inicio_global = time.perf_counter()

        def ejecutar(indice):
            rol, mensaje = PREGUNTAS_REALISTAS[indice % len(PREGUNTAS_REALISTAS)]
            inicio = time.perf_counter()
            resultado = resolve_local_answer(mensaje, rol)
            latencia_ms = (time.perf_counter() - inicio) * 1000

            # Intento deliberado de contaminar el resultado recibido por este hilo.
            resultado["marca_hilo"] = indice
            resultado["llm_error"] = "contaminacion_intencional"
            verificacion = resolve_local_answer(mensaje, rol)
            contaminado = "marca_hilo" in verificacion or "llm_error" in verificacion

            return {
                "ok": resultado.get("action") in {"answer", "clarify", "safe", "fallback_allowed"},
                "rol": rol,
                "accion": resultado.get("action", "desconocida"),
                "intencion": resultado.get("intent", "sin_intencion"),
                "latencia_ms": round(latencia_ms, 3),
                "contaminado": contaminado,
            }

        resultados = []
        errores = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futuros = [executor.submit(ejecutar, indice) for indice in range(total)]
            for futuro in as_completed(futuros):
                try:
                    resultados.append(futuro.result())
                except Exception as exc:  # pragma: no cover - evidencia operacional
                    errores.append(str(exc))

        latencias = [item["latencia_ms"] for item in resultados]
        contaminaciones = sum(1 for item in resultados if item["contaminado"])
        exitosas = sum(1 for item in resultados if item["ok"])
        duracion_ms = (time.perf_counter() - inicio_global) * 1000

        payload = {
            "estado": "ok" if not errores and contaminaciones == 0 else "con_observaciones",
            "solicitudes": total,
            "workers": workers,
            "exitosas": exitosas,
            "errores": errores,
            "contaminaciones_cache": contaminaciones,
            "duracion_total_ms": round(duracion_ms, 3),
            "throughput_aprox_req_s": round((total / duracion_ms) * 1000, 2) if duracion_ms else total,
            "latencia_ms": {
                "min": round(min(latencias), 3) if latencias else 0,
                "p50": _percentil(latencias, 50),
                "p95": _percentil(latencias, 95),
                "max": round(max(latencias), 3) if latencias else 0,
                "promedio": round(sum(latencias) / len(latencias), 3) if latencias else 0,
            },
            "acciones": dict(Counter(item["accion"] for item in resultados)),
            "roles": dict(Counter(item["rol"] for item in resultados)),
            "intenciones_top": dict(Counter(item["intencion"] for item in resultados).most_common(8)),
            "ia_externa_usada": False,
            "nota": "La prueba usa el motor local para medir aislamiento, cache y respuesta sin proveedores externos.",
        }

        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
