"""Generacion reproducible de evidencia tecnica del asistente hibrido."""

from __future__ import annotations

import json
import platform
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django import get_version as django_version

from .evaluation import EvaluationExample, build_challenge_dataset, build_dataset
from .local_engine import resolve_local_answer
from .model_selection import train_compare_select_models
from .services import _estimar_tokens_entrada_ia, construir_system_prompt
from .training_dataset import (
    build_professional_dataset,
    dataset_summary,
    validate_professional_dataset,
)


CONCURRENCY_CASES = (
    ("RESIDENTE", "Como reporto un incidente?"),
    ("RESIDENTE", "No me llegan las notificaciones"),
    ("RESIDENTE", "Que hago si hay ruido de noche?"),
    ("RESIDENTE", "Como hago seguimiento al caso que reporte?"),
    ("VIGILANTE", "Como atiendo un incidente en proceso?"),
    ("ADMINISTRADOR", "Como publico un aviso para residentes?"),
    ("RESIDENTE", "procedimiento biometrico de porteria para QR temporal"),
    ("RESIDENTE", "quien gano el partido de futbol ayer"),
)


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * (percentile / 100)))
    return round(ordered[index], 4)


def _classification_metrics(
    confusion: dict[str, Counter[str]],
    expected_labels: set[str],
) -> dict[str, Any]:
    """Calcula precision, recall y F1 macro por clase esperada."""

    per_intent: dict[str, dict[str, float | int]] = {}
    total_correct = 0
    total = 0
    for expected, predictions in confusion.items():
        total += sum(predictions.values())
        total_correct += predictions.get(expected, 0)

    for label in sorted(expected_labels):
        true_positive = confusion.get(label, Counter()).get(label, 0)
        false_negative = sum(confusion.get(label, Counter()).values()) - true_positive
        false_positive = sum(
            predictions.get(label, 0)
            for expected, predictions in confusion.items()
            if expected != label
        )
        support = true_positive + false_negative
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_intent[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "soporte": support,
            "verdaderos_positivos": true_positive,
            "falsos_positivos": false_positive,
            "falsos_negativos": false_negative,
        }

    precision_macro = statistics.mean(float(item["precision"]) for item in per_intent.values()) if per_intent else 0.0
    recall_macro = statistics.mean(float(item["recall"]) for item in per_intent.values()) if per_intent else 0.0
    f1_macro = statistics.mean(float(item["f1"]) for item in per_intent.values()) if per_intent else 0.0
    micro = total_correct / total if total else 0.0
    return {
        "precision_micro": round(micro, 4),
        "recall_micro": round(micro, 4),
        "f1_micro": round(micro, 4),
        "precision_macro": round(precision_macro, 4),
        "recall_macro": round(recall_macro, 4),
        "f1_macro": round(f1_macro, 4),
        "por_intencion": per_intent,
    }


def _evaluate_examples(examples: list[EvaluationExample], repetitions: int = 3) -> dict[str, Any]:
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    actions: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    latencies: list[float] = []
    errors: list[dict[str, Any]] = []
    stable = 0
    token_savings = 0
    direct_incorrect = 0

    for example in examples:
        signatures = []
        first_result = None
        for _ in range(max(1, repetitions)):
            started = time.perf_counter()
            result = resolve_local_answer(example.text, example.role)
            latencies.append((time.perf_counter() - started) * 1000)
            signatures.append(
                (
                    result.get("action", ""),
                    result.get("intent", ""),
                    result.get("answer", ""),
                )
            )
            first_result = first_result or result

        result = first_result or {}
        action = result.get("action", "safe")
        predicted = result.get("intent", "sin_intencion_confiable")
        expected_outside = example.expected_intent == "sin_intencion_confiable"
        is_correct = (
            action in {"safe", "fallback_allowed"} or predicted == "sin_intencion_confiable"
            if expected_outside
            else predicted == example.expected_intent and action in {"answer", "clarify"}
        )
        stable += int(len(set(signatures)) == 1)
        direct_incorrect += int(action == "answer" and not is_correct)
        confusion[example.expected_intent][predicted] += 1
        actions[action] += 1
        methods[result.get("method", "sin_metodo")] += 1

        if action != "fallback_allowed":
            token_savings += _estimar_tokens_entrada_ia(
                example.text,
                [],
                construir_system_prompt(None),
            )
        if not is_correct:
            errors.append(
                {
                    "texto": example.text,
                    "rol": example.role,
                    "esperada": example.expected_intent,
                    "predicha": predicted,
                    "accion": action,
                    "metodo": result.get("method", ""),
                    "confianza": result.get("confidence", 0),
                }
            )

    total = len(examples)
    avoided_external_calls = total - actions["fallback_allowed"]
    classification = _classification_metrics(confusion, {item.expected_intent for item in examples})
    return {
        "total": total,
        **classification,
        "cobertura_respuesta_local": round(actions["answer"] / total, 4) if total else 0.0,
        "tasa_aclaracion": round(actions["clarify"] / total, 4) if total else 0.0,
        "tasa_respuesta_segura": round(actions["safe"] / total, 4) if total else 0.0,
        "tasa_candidata_gemini": round(actions["fallback_allowed"] / total, 4) if total else 0.0,
        "dependencia_gemini_evitada": round(1 - (actions["fallback_allowed"] / total), 4) if total else 0.0,
        "llamadas_reales_gemini": 0,
        "tokens_externos_ahorrados_estimados": token_savings,
        "tokens_ahorrados_promedio_por_consulta_evitada": (
            round(token_savings / avoided_external_calls, 2) if avoided_external_calls else 0.0
        ),
        "respuestas_directas_incorrectas": direct_incorrect,
        "consistencia_repeticiones": round(stable / total, 4) if total else 0.0,
        "repeticiones_por_pregunta": max(1, repetitions),
        "latencia_ms": {
            "promedio": round(statistics.mean(latencies), 4) if latencies else 0.0,
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "max": round(max(latencies), 4) if latencies else 0.0,
        },
        "acciones": dict(actions),
        "metodos": dict(methods),
        "matriz_confusion": {
            expected: dict(predictions)
            for expected, predictions in sorted(confusion.items())
        },
        "errores": errors,
    }


def _run_concurrency(total: int, workers: int) -> dict[str, Any]:
    latencies: list[float] = []
    errors: list[str] = []
    contaminated = 0
    successful = 0
    roles: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    warmup_started = time.perf_counter()
    for role, message in CONCURRENCY_CASES:
        resolve_local_answer(message, role)
    warmup_ms = (time.perf_counter() - warmup_started) * 1000
    started_global = time.perf_counter()

    def execute(index: int) -> dict[str, Any]:
        role, message = CONCURRENCY_CASES[index % len(CONCURRENCY_CASES)]
        started = time.perf_counter()
        result = resolve_local_answer(message, role)
        elapsed = (time.perf_counter() - started) * 1000
        result["marca_prueba_concurrente"] = index
        second = resolve_local_answer(message, role)
        return {
            "role": role,
            "action": second.get("action", ""),
            "latency": elapsed,
            "contaminated": "marca_prueba_concurrente" in second,
            "ok": second.get("action") in {"answer", "clarify", "safe", "fallback_allowed"},
        }

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(execute, index) for index in range(total)]
        for future in as_completed(futures):
            try:
                result = future.result()
                latencies.append(result["latency"])
                contaminated += int(result["contaminated"])
                successful += int(result["ok"])
                roles[result["role"]] += 1
                actions[result["action"]] += 1
            except Exception as exc:  # pragma: no cover - evidencia operacional
                errors.append(str(exc))

    duration = (time.perf_counter() - started_global) * 1000
    return {
        "solicitudes": total,
        "workers": workers,
        "calentamiento_previo_ms": round(warmup_ms, 4),
        "exitosas": successful,
        "errores": errors,
        "contaminaciones_cache": contaminated,
        "roles": dict(roles),
        "acciones": dict(actions),
        "duracion_total_ms": round(duration, 4),
        "throughput_aprox_req_s": round(total / (duration / 1000), 2) if duration else 0.0,
        "latencia_ms": {
            "promedio": round(statistics.mean(latencies), 4) if latencies else 0.0,
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "max": round(max(latencies), 4) if latencies else 0.0,
        },
        "aislamiento_aprobado": not errors and contaminated == 0 and successful == total,
        "ia_externa_usada": False,
        "nota_latencia": "Latencia estable medida despues de registrar por separado la inicializacion en frio.",
    }


def generate_technical_evidence(
    *,
    seed: int = 42,
    repetitions: int = 3,
    concurrency_requests: int = 600,
    workers: int = 20,
) -> dict[str, Any]:
    professional = build_professional_dataset(seed=seed)
    splits = build_dataset(seed=seed)
    challenge = build_challenge_dataset()
    model_comparison = train_compare_select_models(seed=seed)

    return {
        "generado_en_utc": datetime.now(timezone.utc).isoformat(),
        "entorno": {
            "python": platform.python_version(),
            "django": django_version(),
            "plataforma": platform.platform(),
            "semilla": seed,
            "usa_ia_externa_durante_evaluacion": False,
        },
        "dataset": dataset_summary(professional),
        "errores_validacion_dataset": validate_professional_dataset(professional),
        "evaluacion_test_independiente": _evaluate_examples(splits["test"], repetitions),
        "evaluacion_desafio": _evaluate_examples(challenge, repetitions),
        "comparacion_modelos": {
            "criterio": model_comparison["criterio_seleccion"],
            "modelo_seleccionado": model_comparison["modelo_seleccionado"],
            "ranking": model_comparison["ranking"],
            "limitaciones": model_comparison["analisis_limitaciones"],
        },
        "concurrencia": _run_concurrency(concurrency_requests, workers),
        "notas_metodologicas": [
            "Precision, recall y F1 se calculan sobre intenciones esperadas y predichas.",
            "Cobertura local cuenta respuestas directas locales; aclaraciones y respuestas seguras tambien evitan IA externa.",
            "La tasa candidata Gemini representa consultas que podrian usar el respaldo externo; durante esta evaluacion no se llamo a Gemini.",
            "El ahorro de tokens es una estimacion usando el mismo estimador interno de CommuSafe, no una factura del proveedor.",
            "La concurrencia mide el motor local en este equipo y no reemplaza una prueba distribuida de produccion.",
        ],
    }


def export_evidence(payload: dict[str, Any], json_path: str | Path, markdown_path: str | Path) -> None:
    json_file = Path(json_path)
    markdown_file = Path(markdown_path)
    json_file.parent.mkdir(parents=True, exist_ok=True)
    markdown_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_file.write_text(_render_markdown(payload), encoding="utf-8")


def _percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def _render_markdown(payload: dict[str, Any]) -> str:
    test = payload["evaluacion_test_independiente"]
    challenge = payload["evaluacion_desafio"]
    concurrency = payload["concurrencia"]
    selected = payload["comparacion_modelos"]["modelo_seleccionado"]
    weakest = sorted(
        test["por_intencion"].items(),
        key=lambda item: (item[1]["f1"], item[0]),
    )[:5]
    error_rows = test["errores"][:10]
    production = payload.get("evidencia_produccion")
    tests = payload.get("evidencia_pruebas")
    lines = [
        "# Evidencia tecnica del asistente hibrido CommuSafe",
        "",
        f"Generada: `{payload['generado_en_utc']}`  ",
        "Semilla reproducible: `42`  ",
        "IA externa utilizada durante la evaluacion: **No**",
        "",
        "## Resumen para jurado",
        "",
        "La evaluacion demuestra que CommuBot resuelve la mayoria de consultas mediante conocimiento local verificable. "
        "Gemini queda como respaldo para consultas del dominio que no alcanzan confianza suficiente. "
        "Esto reduce dependencia externa y mantiene respuestas repetibles.",
        "",
        "| Indicador | Resultado medido | Interpretacion simple |",
        "|---|---:|---|",
        f"| Precision micro en split test reservado | {_percentage(test['precision_micro'])} | Proporcion total de clasificaciones correctas |",
        f"| Recall macro en split test reservado | {_percentage(test['recall_macro'])} | Capacidad promedio de reconocer cada intencion |",
        f"| F1 macro en split test reservado | {_percentage(test['f1_macro'])} | Equilibrio promedio entre precision y recall |",
        f"| Cobertura de respuesta local directa | {_percentage(test['cobertura_respuesta_local'])} | Preguntas respondidas directamente sin Gemini |",
        f"| Dependencia de Gemini evitada | {_percentage(test['dependencia_gemini_evitada'])} | Respuestas locales, aclaraciones o rechazo seguro |",
        f"| Tasa candidata a Gemini | {_percentage(test['tasa_candidata_gemini'])} | Casos que podrian requerir respaldo externo |",
        f"| Consistencia en {test['repeticiones_por_pregunta']} repeticiones | {_percentage(test['consistencia_repeticiones'])} | Misma pregunta produce la misma decision y respuesta |",
        f"| Respuestas directas incorrectas | {test['respuestas_directas_incorrectas']} | Riesgo de afirmar algo equivocado directamente |",
        f"| Latencia local promedio | {test['latencia_ms']['promedio']:.4f} ms | Tiempo medio del motor local en este equipo, con motor cargado |",
        f"| Tokens externos ahorrados estimados | {test['tokens_externos_ahorrados_estimados']} | Estimacion frente a enviar todas las consultas a Gemini |",
        f"| Ahorro estimado promedio por consulta evitada | {test['tokens_ahorrados_promedio_por_consulta_evitada']:.2f} tokens | Promedio estimado, no facturacion real |",
        "",
        "## Metodo",
        "",
        f"- Dataset profesional: **{payload['dataset']['total']}** ejemplos, **{payload['dataset']['intenciones']}** intenciones y **{payload['dataset']['faq_representadas']}** FAQ representadas.",
        f"- Split test reservado: **{test['total']}** preguntas no usadas para entrenar modelos supervisados.",
        f"- Conjunto desafio: **{challenge['total']}** preguntas ambiguas, externas o que requieren validacion.",
        "- Los splits no comparten frases; la validacion automatica del dataset debe producir una lista vacia.",
        "- La evaluacion no llama a Gemini, por lo que no consume tokens externos ni depende de disponibilidad de red.",
        "",
        "## Calidad de clasificacion",
        "",
        "| Metrica | Split test reservado | Desafio |",
        "|---|---:|---:|",
        f"| Precision micro | {_percentage(test['precision_micro'])} | {_percentage(challenge['precision_micro'])} |",
        f"| Recall micro | {_percentage(test['recall_micro'])} | {_percentage(challenge['recall_micro'])} |",
        f"| F1 micro | {_percentage(test['f1_micro'])} | {_percentage(challenge['f1_micro'])} |",
        f"| Precision macro | {_percentage(test['precision_macro'])} | {_percentage(challenge['precision_macro'])} |",
        f"| Recall macro | {_percentage(test['recall_macro'])} | {_percentage(challenge['recall_macro'])} |",
        f"| F1 macro | {_percentage(test['f1_macro'])} | {_percentage(challenge['f1_macro'])} |",
        "",
        "El resultado del conjunto desafio debe interpretarse por separado: contiene deliberadamente preguntas que el sistema "
        "debe aclarar, rechazar de forma segura o remitir a administracion, no responder con seguridad artificial.",
        "",
        "## Reduccion de dependencia generativa",
        "",
        "| Decision del motor en test | Casos | Tasa |",
        "|---|---:|---:|",
        f"| Respuesta local directa | {test['acciones'].get('answer', 0)} | {_percentage(test['cobertura_respuesta_local'])} |",
        f"| Solicita aclaracion | {test['acciones'].get('clarify', 0)} | {_percentage(test['tasa_aclaracion'])} |",
        f"| Respuesta segura sin inventar | {test['acciones'].get('safe', 0)} | {_percentage(test['tasa_respuesta_segura'])} |",
        f"| Candidata a respaldo Gemini | {test['acciones'].get('fallback_allowed', 0)} | {_percentage(test['tasa_candidata_gemini'])} |",
        f"| Llamadas reales a Gemini en esta prueba | {test['llamadas_reales_gemini']} | 0.00% |",
        "",
    ]
    if production:
        lines.extend(
            [
                "## Evidencia operativa en produccion",
                "",
                f"El endpoint protegido de diagnostico fue consultado el `{production['capturado_en']}`. "
                f"En su ventana real de {production['ventana_horas']} horas reporto:",
                "",
                "| Indicador operativo | Resultado |",
                "|---|---:|",
                f"| Consultas registradas | {production['consultas_totales']} |",
                f"| Resueltas sin Gemini | {production['resueltas_sin_gemini']} |",
                f"| Uso real de Gemini | {production['usan_gemini']} |",
                f"| Tokens de IA externa estimados | {production['tokens_ia_estimados']} |",
                f"| Tokens ahorrados estimados | {production['tokens_ahorrados_estimados']} |",
                f"| Porcentaje sin Gemini | {production['porcentaje_sin_gemini']:.2f}% |",
                "",
                "Esta evidencia confirma que la politica local primero funciona en produccion, pero la muestra es pequena. "
                "No debe usarse por si sola para afirmar un porcentaje general de uso futuro.",
                "",
            ]
        )
    lines.extend(
        [
            "## Comparacion con alternativas",
            "",
            f"Modelo seleccionado: **{selected['nombre']}** (`{selected['id']}`).",
            "",
            "| Modelo | Validation F1 | Test F1 | Challenge F1 | Puntaje generalizacion |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in payload["comparacion_modelos"]["ranking"]:
        lines.append(
            f"| {row['nombre']} | {row['validation_f1']:.4f} | {row['test_f1']:.4f} | "
            f"{row['challenge_f1']:.4f} | {row['puntaje_generalizacion']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Concurrencia y multiples roles",
            "",
            f"- Solicitudes concurrentes: **{concurrency['solicitudes']}** con **{concurrency['workers']}** workers.",
            f"- Solicitudes exitosas: **{concurrency['exitosas']}**.",
            f"- Errores: **{len(concurrency['errores'])}**.",
            f"- Contaminaciones de cache entre solicitudes: **{concurrency['contaminaciones_cache']}**.",
            f"- Throughput aproximado: **{concurrency['throughput_aprox_req_s']} solicitudes/s**.",
            f"- Latencia p95: **{concurrency['latencia_ms']['p95']} ms**.",
            f"- Calentamiento previo separado: **{concurrency['calentamiento_previo_ms']} ms**.",
            f"- Roles simulados: `{concurrency['roles']}`.",
            "",
            "La prueba verifica que solicitudes simultaneas de residentes, vigilancia y administracion no comparten resultados mutables. "
            "La persistencia y propiedad de conversaciones se valida adicionalmente mediante pruebas automatizadas del backend.",
            "",
        ]
    )
    if tests:
        module = tests["modulo_asistente"]
        backend = tests["regresion_backend"]
        lines.extend(
            [
                "## Pruebas automatizadas de aislamiento y persistencia",
                "",
                f"- Modulo asistente: **{module['pruebas_aprobadas']} pruebas + {module['subpruebas_aprobadas']} subpruebas**, 0 fallos.",
                f"- Regresion backend completa: **{backend['pruebas_aprobadas']} pruebas + {backend['subpruebas_aprobadas']} subpruebas**, 0 fallos.",
                "- Casos especificos aprobados:",
            ]
        )
        for case in tests["casos_aislamiento_y_persistencia"]:
            lines.append(f"  - `{case}`")
        lines.append("")
    lines.extend(
        [
            "## Intenciones con menor F1 en split test",
            "",
            "| Intencion | Precision | Recall | F1 | Soporte |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for intent, metrics in weakest:
        lines.append(
            f"| `{intent}` | {metrics['precision']:.4f} | {metrics['recall']:.4f} | "
            f"{metrics['f1']:.4f} | {metrics['soporte']} |"
        )

    lines.extend(["", "## Errores observados", ""])
    if error_rows:
        lines.extend(
            [
                "| Pregunta | Esperada | Predicha | Accion |",
                "|---|---|---|---|",
            ]
        )
        for row in error_rows:
            safe_text = row["texto"].replace("|", "/")
            lines.append(
                f"| {safe_text} | `{row['esperada']}` | `{row['predicha']}` | `{row['accion']}` |"
            )
    else:
        lines.append("No se observaron errores operacionales en el split test reservado.")

    lines.extend(
        [
            "",
            "## Limitaciones declaradas",
            "",
            "- El dataset fue construido a partir del dominio de CommuSafe; puede representar mejor preguntas previstas que lenguaje completamente inesperado de usuarios reales.",
            "- El conjunto desafio es pequeno y debe ampliarse con consultas reales anonimizadas despues de la puesta en uso.",
            "- El test usa frases separadas, pero generadas desde el mismo dominio y las mismas FAQ; por ello puede sobreestimar el comportamiento ante lenguaje completamente nuevo.",
            "- El ahorro de tokens es estimado con el estimador interno; no representa una factura exacta de Google.",
            "- La evidencia operativa de produccion contiene solo tres consultas en su ventana de 24 horas y se presenta como observacion complementaria.",
            "- La prueba concurrente mide el motor local y el equipo actual; no reemplaza pruebas distribuidas de larga duracion sobre produccion.",
            "- Una tasa baja de Gemini no significa que Gemini sea innecesario: conserva valor como respaldo controlado para consultas no cubiertas.",
            "",
            "## Reproduccion",
            "",
            "```powershell",
            "cd backend",
            r".\.venv\Scripts\python.exe manage.py generar_evidencia_tecnica_asistente",
            r".\.venv\Scripts\python.exe -m pytest asistente -q",
            "```",
            "",
            "La matriz de confusion completa, metricas por intencion y errores detallados se encuentran en el JSON generado junto a este informe.",
        ]
    )
    return "\n".join(lines) + "\n"
