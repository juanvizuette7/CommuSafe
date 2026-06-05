"""Evaluacion reproducible del motor local de CommuBot."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .local_engine import DOMAIN_TERMS, ENGINE, MEDIUM_CONFIDENCE_THRESHOLD, normalize_text, tokenize
from .local_knowledge import FAQ_ENTRIES


@dataclass(frozen=True)
class EvaluationExample:
    text: str
    expected_intent: str
    category: str
    role: str = "RESIDENTE"


def build_dataset(seed: int = 42) -> dict[str, list[EvaluationExample]]:
    """Construye split deterministico train/validation/test desde la base local."""

    examples: list[EvaluationExample] = []
    for entry in FAQ_ENTRIES:
        role = entry.allowed_roles[0]
        examples.append(EvaluationExample(entry.question, entry.intent, entry.category, role))
        for variation in entry.variations:
            examples.append(EvaluationExample(variation, entry.intent, entry.category, role))

    random.Random(seed).shuffle(examples)
    total = len(examples)
    train_end = int(total * 0.70)
    validation_end = int(total * 0.85)
    splits = {
        "train": examples[:train_end],
        "validation": examples[train_end:validation_end],
        "test": examples[validation_end:],
    }
    splits["test"].extend(
        [
            EvaluationExample("quien gano el partido de futbol ayer", "sin_intencion_confiable", "fuera_contexto"),
            EvaluationExample("precio del dolar hoy en colombia", "sin_intencion_confiable", "fuera_contexto"),
            EvaluationExample("hazme una receta de pasta", "sin_intencion_confiable", "fuera_contexto"),
            EvaluationExample("quiero saber algo del parqueadero y visitantes", "vehiculo_visitante", "ambigua"),
            EvaluationExample("tengo una duda con un reporte y una alerta", "consultar_estado_incidente", "ambigua"),
            EvaluationExample("cuanto vale exactamente la multa por ruido", "pagos_cuotas", "requiere_validacion"),
            EvaluationExample("cual es el celular directo del administrador", "telefono_administracion", "requiere_validacion"),
        ]
    )
    return splits


def evaluate_split(examples: list[EvaluationExample]) -> dict[str, Any]:
    """Evalua recuperacion top-1 e identifica aclaraciones/respuestas seguras."""

    total = len(examples)
    correct = 0
    local_answers = 0
    clarifications = 0
    safe_answers = 0
    generative_candidates = 0
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    latencies = []

    for example in examples:
        result = ENGINE.resolve(example.text, example.role)
        predicted = result.get("intent", "sin_intencion_confiable")
        action = result.get("action", "")
        if example.expected_intent == "sin_intencion_confiable":
            if action in {"safe", "fallback_allowed"} or predicted == "sin_intencion_confiable":
                correct += 1
        elif predicted == example.expected_intent and action in {"answer", "clarify"}:
            correct += 1
        if action == "answer":
            local_answers += 1
        elif action == "clarify":
            clarifications += 1
        elif action == "safe":
            safe_answers += 1
        elif action == "fallback_allowed":
            generative_candidates += 1
        confusion[example.expected_intent][predicted] += 1
        latencies.append(result.get("latency_ms", 0))

    accuracy = correct / total if total else 0
    local_coverage = local_answers / total if total else 0
    clarification_rate = clarifications / total if total else 0
    safe_rate = safe_answers / total if total else 0
    generative_rate = generative_candidates / total if total else 0

    # En clasificacion monolabel con recuperacion top-1, micro precision,
    # recall y F1 equivalen a accuracy sobre el split evaluado.
    return {
        "total": total,
        "correctas": correct,
        "precision_micro": round(accuracy, 4),
        "recall_micro": round(accuracy, 4),
        "f1_micro": round(accuracy, 4),
        "cobertura_local": round(local_coverage, 4),
        "tasa_aclaracion": round(clarification_rate, 4),
        "tasa_respuesta_segura": round(safe_rate, 4),
        "tasa_uso_ia_estimado": round(generative_rate, 4),
        "latencia_promedio_ms": round(sum(latencies) / total, 2) if total else 0,
        "matriz_confusion_resumen": {
            expected: dict(predicted_counter.most_common(5))
            for expected, predicted_counter in sorted(confusion.items())
        },
    }


def _prediccion_por_estrategia(example: EvaluationExample, strategy: str) -> str:
    """Predice intencion con estrategias comparables de recuperacion local."""

    if strategy == "hibrido_seleccionado":
        return ENGINE.resolve(example.text, example.role).get("intent", "sin_intencion_confiable")

    normalized = normalize_text(example.text)
    query_tokens = set(tokenize(normalized))
    if query_tokens and not (query_tokens & DOMAIN_TERMS):
        return "sin_intencion_confiable"

    candidates = ENGINE._score_candidates(normalized, example.role)  # noqa: SLF001 - evaluacion interna controlada.
    if not candidates:
        return "sin_intencion_confiable"

    if strategy == "palabras_clave_baseline":
        best = max(candidates, key=lambda item: item["score_parts"]["keywords"])
        confidence = best["score_parts"]["keywords"]
    elif strategy == "tfidf_semantico":
        best = max(candidates, key=lambda item: item["score_parts"]["semantica"])
        confidence = best["score_parts"]["semantica"]
    else:
        best = candidates[0]
        confidence = best["confidence"]

    if confidence < MEDIUM_CONFIDENCE_THRESHOLD:
        return "sin_intencion_confiable"
    return best["entry"].intent


def compare_models(examples: list[EvaluationExample]) -> dict[str, Any]:
    """Compara estrategias locales y documenta la seleccion del motor final."""

    strategies = ["palabras_clave_baseline", "tfidf_semantico", "hibrido_seleccionado"]
    results: dict[str, Any] = {}
    for strategy in strategies:
        total = len(examples)
        correct = 0
        confusion: dict[str, Counter[str]] = defaultdict(Counter)
        for example in examples:
            predicted = _prediccion_por_estrategia(example, strategy)
            if predicted == example.expected_intent:
                correct += 1
            confusion[example.expected_intent][predicted] += 1

        score = correct / total if total else 0
        results[strategy] = {
            "total": total,
            "correctas": correct,
            "precision_micro": round(score, 4),
            "recall_micro": round(score, 4),
            "f1_micro": round(score, 4),
            "matriz_confusion_resumen": {
                expected: dict(predicted_counter.most_common(3))
                for expected, predicted_counter in sorted(confusion.items())
            },
        }
    results["seleccion"] = (
        "Se selecciona hibrido_seleccionado porque combina coincidencia exacta, "
        "palabras clave, similitud TF-IDF, filtro de dominio y umbrales de aclaracion."
    )
    return results


def evaluate_all() -> dict[str, Any]:
    splits = build_dataset()
    return {
        "dataset": {name: len(values) for name, values in splits.items()},
        "train": evaluate_split(splits["train"]),
        "validation": evaluate_split(splits["validation"]),
        "test": evaluate_split(splits["test"]),
        "comparacion_modelos": {
            "validation": compare_models(splits["validation"]),
            "test": compare_models(splits["test"]),
        },
        "nota": (
            "Metricas calculadas localmente sobre preguntas y variaciones registradas. "
            "No sustituyen pruebas con usuarios reales, pero evidencian cobertura inicial."
        ),
    }
