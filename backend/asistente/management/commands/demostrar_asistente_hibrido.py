"""Recorrido verificable para la demostracion academica de CommuBot."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from asistente.local_engine import resolve_local_answer
from asistente.services import (
    _llm_backup_enabled,
    _resolver_adaptador_proveedor,
    generar_respuesta_asistente,
    metricas_uso_asistente,
)
from asistente.technical_evidence import _run_concurrency


@dataclass(frozen=True)
class DemoCase:
    codigo: str
    titulo: str
    mensaje: str
    accion_local_esperada: str
    explicacion: str


DEMO_CASES = (
    DemoCase(
        codigo="local_conocida",
        titulo="Pregunta conocida respondida localmente",
        mensaje="¿Cómo reporto un incidente?",
        accion_local_esperada="answer",
        explicacion="La coincidencia local entrega una respuesta verificada sin consumir Gemini.",
    ),
    DemoCase(
        codigo="variacion_natural",
        titulo="Variación informal de redacción",
        mensaje="Parce, no puedo entrar a la cuenta, ¿qué hago?",
        accion_local_esperada="answer",
        explicacion="Las reglas y la normalización reconocen una forma informal no idéntica a la FAQ.",
    ),
    DemoCase(
        codigo="error_ortografico",
        titulo="Pregunta con error ortográfico",
        mensaje="Komo reporto un insidente",
        accion_local_esperada="answer",
        explicacion="La normalización permite comprender errores frecuentes sin usar IA externa.",
    ),
    DemoCase(
        codigo="ambigua",
        titulo="Pregunta ambigua que solicita aclaración",
        mensaje="Música alta",
        accion_local_esperada="clarify",
        explicacion="El asistente reconoce que existen varias interpretaciones y evita asumir.",
    ),
    DemoCase(
        codigo="gemini_respaldo",
        titulo="Consulta del dominio candidata a Gemini",
        mensaje="¿Cuál es el procedimiento oficial para activar un código QR temporal biométrico en portería?",
        accion_local_esperada="fallback_allowed",
        explicacion="El motor local no encuentra conocimiento suficiente y habilita el respaldo controlado.",
    ),
    DemoCase(
        codigo="desconocida_segura",
        titulo="Consulta desconocida fuera del dominio",
        mensaje="¿Quién ganó el partido de fútbol ayer?",
        accion_local_esperada="safe",
        explicacion="El asistente limita su alcance y responde de forma segura sin Gemini.",
    ),
)


class Command(BaseCommand):
    help = "Ejecuta el recorrido academico verificable del asistente hibrido."

    def add_arguments(self, parser):
        parser.add_argument(
            "--usar-gemini",
            action="store_true",
            help="Ejecuta una llamada real y controlada a Gemini para el caso de respaldo.",
        )
        parser.add_argument(
            "--solicitudes",
            type=int,
            default=60,
            help="Solicitudes concurrentes simuladas para la demostracion multiusuario.",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=6,
            help="Trabajadores concurrentes de la simulacion multiusuario.",
        )
        parser.add_argument(
            "--json",
            dest="json_path",
            default="",
            help="Ruta opcional para guardar la evidencia de la ejecucion.",
        )

    def handle(self, *args, **options):
        usar_gemini = bool(options["usar_gemini"])
        solicitudes = max(3, int(options["solicitudes"]))
        workers = max(1, int(options["workers"]))
        proveedor = _resolver_adaptador_proveedor()
        metricas_antes = metricas_uso_asistente(24)

        self.stdout.write(self.style.MIGRATE_HEADING("DEMOSTRACION ACADEMICA DEL ASISTENTE HIBRIDO"))
        self.stdout.write(
            f"Proveedor de respaldo: {proveedor.name} | Modelo: {proveedor.model} | "
            f"Configurado: {'sí' if proveedor.configured else 'no'} | "
            f"Respaldo habilitado: {'sí' if _llm_backup_enabled() else 'no'}"
        )
        self.stdout.write("")

        resultados = []
        errores = []
        for indice, caso in enumerate(DEMO_CASES, start=1):
            local = resolve_local_answer(caso.mensaje, "RESIDENTE")
            cumple_local = local.get("action") == caso.accion_local_esperada
            resultado_final = None
            if caso.codigo == "gemini_respaldo":
                if usar_gemini:
                    resultado_final = generar_respuesta_asistente(caso.mensaje)
                    cumple_final = (
                        resultado_final.get("modo") == "ia"
                        and resultado_final.get("proveedor") == "gemini"
                    )
                else:
                    cumple_final = cumple_local
            else:
                resultado_final = generar_respuesta_asistente(caso.mensaje)
                cumple_final = cumple_local

            cumple = cumple_local and cumple_final
            if not cumple:
                errores.append(caso.codigo)
            item = {
                "codigo": caso.codigo,
                "titulo": caso.titulo,
                "mensaje": caso.mensaje,
                "explicacion": caso.explicacion,
                "decision_local": {
                    "accion": local.get("action", ""),
                    "intencion": local.get("intent", ""),
                    "confianza": local.get("confidence", 0),
                    "metodo": local.get("method", ""),
                },
                "resultado_final": {
                    "modo": (resultado_final or {}).get("modo", "preclasificacion_local"),
                    "proveedor": (resultado_final or {}).get("proveedor", "local"),
                    "modelo": (resultado_final or {}).get("modelo_usado", local.get("model", "")),
                    "respuesta": (resultado_final or {}).get(
                        "respuesta",
                        "La llamada real a Gemini no se ejecuto. Usa --usar-gemini para validarla.",
                    ),
                },
                "cumple": cumple,
            }
            resultados.append(item)
            estado = self.style.SUCCESS("OK") if cumple else self.style.ERROR("FALLO")
            self.stdout.write(self.style.HTTP_INFO(f"{indice}. {caso.titulo} [{estado}]"))
            self.stdout.write(f"   Pregunta: {caso.mensaje}")
            self.stdout.write(
                f"   Decisión local: {local.get('action')} | Intención: {local.get('intent')} | "
                f"Confianza: {local.get('confidence')} | Método: {local.get('method')}"
            )
            if resultado_final:
                self.stdout.write(
                    f"   Resultado final: {resultado_final.get('modo')} | "
                    f"Proveedor: {resultado_final.get('proveedor')} | "
                    f"Modelo: {resultado_final.get('modelo_usado')}"
                )
                self.stdout.write(f"   Respuesta: {resultado_final.get('respuesta')}")
            else:
                self.stdout.write("   Gemini preparado, pero no invocado en esta ejecución.")
            self.stdout.write(f"   Valor técnico: {caso.explicacion}")
            self.stdout.write("")

        concurrencia = _run_concurrency(solicitudes, workers)
        metricas_despues = metricas_uso_asistente(24)
        resumen_ejecucion = self._resumir_ejecucion(resultados)
        proveedor_listo = proveedor.configured and _llm_backup_enabled()
        gemini_verificado = any(
            item["codigo"] == "gemini_respaldo"
            and item["resultado_final"]["modo"] == "ia"
            and item["resultado_final"]["proveedor"] == "gemini"
            for item in resultados
        )
        criterios = {
            "casos_funcionales_cumplen": not errores,
            "proveedor_respaldo_preparado": proveedor_listo,
            "gemini_real_verificado": gemini_verificado if usar_gemini else None,
            "concurrencia_sin_errores": concurrencia["exitosas"] == solicitudes and not concurrencia["errores"],
            "sin_contaminacion_cache": concurrencia["contaminaciones_cache"] == 0,
            "aislamiento_concurrente_aprobado": concurrencia["aislamiento_aprobado"],
        }
        payload = {
            "generado_en_utc": datetime.now(timezone.utc).isoformat(),
            "estado": "listo" if all(valor is not False for valor in criterios.values()) else "con_observaciones",
            "gemini_real_solicitado": usar_gemini,
            "proveedor": {
                "nombre": proveedor.name,
                "modelo": proveedor.model,
                "configurado": proveedor.configured,
                "respaldo_habilitado": _llm_backup_enabled(),
            },
            "casos": resultados,
            "metricas_operativas_24h_antes": metricas_antes,
            "metricas_operativas_24h_despues": metricas_despues,
            "resumen_ejecucion_demo": resumen_ejecucion,
            "concurrencia": concurrencia,
            "criterios": criterios,
        }

        self.stdout.write(self.style.MIGRATE_HEADING("METRICAS OPERATIVAS AUTENTICADAS DE LAS ULTIMAS 24 HORAS"))
        self.stdout.write(json.dumps(metricas_despues, ensure_ascii=False, indent=2))
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("RESUMEN AISLADO DE ESTA DEMOSTRACION"))
        self.stdout.write(json.dumps(resumen_ejecucion, ensure_ascii=False, indent=2))
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("SIMULACION CON VARIOS ROLES"))
        self.stdout.write(
            json.dumps(
                {
                    "solicitudes": concurrencia["solicitudes"],
                    "workers": concurrencia["workers"],
                    "exitosas": concurrencia["exitosas"],
                    "errores": concurrencia["errores"],
                    "contaminaciones_cache": concurrencia["contaminaciones_cache"],
                    "roles": concurrencia["roles"],
                    "aislamiento_aprobado": concurrencia["aislamiento_aprobado"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        if options["json_path"]:
            output = Path(options["json_path"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Evidencia guardada en: {output}"))

        if errores:
            raise CommandError(f"No cumplieron los casos: {', '.join(errores)}")
        if usar_gemini and not gemini_verificado:
            raise CommandError(
                "Gemini no produjo una respuesta aceptada. El sistema mantuvo la respuesta segura; "
                "revisa proveedor, cuota y conectividad antes de la demostracion."
            )
        if not concurrencia["aislamiento_aprobado"]:
            raise CommandError("La simulacion concurrente no aprobo el aislamiento esperado.")

        self.stdout.write(self.style.SUCCESS("ASISTENTE LISTO PARA LA DEMOSTRACION ACADEMICA."))

    @staticmethod
    def _resumir_ejecucion(resultados):
        modos = {}
        proveedores = {}
        for item in resultados:
            modo = item["resultado_final"]["modo"]
            proveedor = item["resultado_final"]["proveedor"]
            modos[modo] = modos.get(modo, 0) + 1
            proveedores[proveedor] = proveedores.get(proveedor, 0) + 1
        return {
            "casos": len(resultados),
            "modos": modos,
            "proveedores": proveedores,
            "nota": "Este resumen pertenece solo al comando de demostracion y no altera las metricas operativas autenticadas.",
        }
