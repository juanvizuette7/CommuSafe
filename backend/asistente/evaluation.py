"""Evaluacion reproducible del motor local de CommuBot."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .local_engine import (
    AMBIGUITY_MARGIN,
    DOMAIN_TERMS,
    ENGINE,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    normalize_text,
    tokenize,
)
from .training_dataset import build_professional_dataset, dataset_summary, validate_professional_dataset


@dataclass(frozen=True)
class EvaluationExample:
    text: str
    expected_intent: str
    category: str
    role: str = "RESIDENTE"


def build_dataset(seed: int = 42) -> dict[str, list[EvaluationExample]]:
    """Construye split deterministico train/validation/test profesional."""

    professional_splits = build_professional_dataset(seed=seed)
    return {
        split: [
            EvaluationExample(example.text, example.intent, example.category, example.role)
            for example in examples
        ]
        for split, examples in professional_splits.items()
    }


def build_challenge_dataset() -> list[EvaluationExample]:
    """Casos dificiles fuera del entrenamiento para medir rechazo y ambiguedad."""

    return [
        EvaluationExample("quien gano el partido de futbol ayer", "sin_intencion_confiable", "fuera_contexto"),
        EvaluationExample("precio del dolar hoy en colombia", "sin_intencion_confiable", "fuera_contexto"),
        EvaluationExample("hazme una receta de pasta", "sin_intencion_confiable", "fuera_contexto"),
        EvaluationExample("quiero saber algo del parqueadero y visitantes", "visitantes_ingresos", "ambigua"),
        EvaluationExample("tengo una duda con un reporte y una alerta", "seguimiento_incidente", "ambigua"),
        EvaluationExample("cuanto vale exactamente la multa por ruido", "tramites_administrativos", "requiere_validacion"),
        EvaluationExample("cual es el celular directo del administrador", "tramites_administrativos", "requiere_validacion"),
    ]


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
    confusion_pairs = [
        {
            "esperada": expected,
            "predicha": predicted,
            "casos": count,
        }
        for expected, predicted_counter in confusion.items()
        for predicted, count in predicted_counter.items()
        if expected != predicted
    ]
    confusion_pairs.sort(key=lambda item: (-item["casos"], item["esperada"], item["predicha"]))

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
        "confusiones_principales": confusion_pairs[:10],
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
    return best["entry"].main_intent


def _decision_con_umbrales(
    example: EvaluationExample,
    high_threshold: float,
    medium_threshold: float,
    ambiguity_margin: float,
) -> tuple[str, str]:
    """Simula la politica del motor para calibrar umbrales reproduciblemente."""

    normalized = normalize_text(example.text)
    exact_entries = [
        entry
        for entry in ENGINE._exact_index.get(normalized, [])  # noqa: SLF001 - calibracion interna controlada.
        if ENGINE._role_allowed(entry, example.role)  # noqa: SLF001
    ]
    if len(exact_entries) == 1:
        return exact_entries[0].main_intent, "answer"
    if len(exact_entries) > 1:
        return exact_entries[0].main_intent, "clarify"

    query_tokens = set(tokenize(normalized))
    if query_tokens and not (query_tokens & DOMAIN_TERMS):
        return "sin_intencion_confiable", "safe"

    candidates = ENGINE._score_candidates(normalized, example.role)  # noqa: SLF001
    if not candidates:
        return "sin_intencion_confiable", "safe"

    best = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None
    confidence = best["confidence"]
    predicted = best["entry"].main_intent
    ambiguous = bool(
        second
        and best["entry"].main_intent != second["entry"].main_intent
        and (confidence - second["confidence"]) < ambiguity_margin
    )

    if confidence >= high_threshold and not ambiguous:
        return predicted, "answer"
    if confidence >= medium_threshold:
        return predicted, "clarify"
    return predicted, "fallback_allowed"


def calibrate_thresholds(
    validation_examples: list[EvaluationExample],
    challenge_examples: list[EvaluationExample],
) -> dict[str, Any]:
    """Busca umbrales que priorizan exactitud local y evitan respuestas incorrectas."""

    best_result: dict[str, Any] | None = None
    high_values = [round(value / 100, 2) for value in range(52, 73, 2)]
    medium_values = [round(value / 100, 2) for value in range(28, 51, 2)]
    margin_values = [round(value / 100, 2) for value in range(4, 13, 2)]
    examples = validation_examples + challenge_examples

    for high in high_values:
        for medium in medium_values:
            if medium >= high:
                continue
            for margin in margin_values:
                correct = 0
                wrong_direct_answers = 0
                local_answers = 0
                clarifications = 0
                fallbacks = 0
                safe_answers = 0
                utility = 0.0

                for example in examples:
                    predicted, action = _decision_con_umbrales(example, high, medium, margin)
                    expected_outside = example.expected_intent == "sin_intencion_confiable"
                    is_correct = (
                        predicted == example.expected_intent
                        or (expected_outside and action == "safe")
                    )
                    correct += int(is_correct)
                    local_answers += int(action == "answer")
                    clarifications += int(action == "clarify")
                    fallbacks += int(action == "fallback_allowed")
                    safe_answers += int(action == "safe")
                    wrong_direct_answers += int(action == "answer" and not is_correct)

                    if action == "answer":
                        utility += 1.0 if is_correct else -1.5
                    elif action == "clarify":
                        utility += 0.75 if is_correct else -0.15
                    elif action == "safe":
                        utility += 1.0 if expected_outside else -0.5
                    else:
                        utility += 0.25 if is_correct else -0.2

                candidate = {
                    "umbral_alto": high,
                    "umbral_medio": medium,
                    "margen_ambiguedad": margin,
                    "utilidad": round(utility, 4),
                    "exactitud": round(correct / len(examples), 4),
                    "respuestas_locales": local_answers,
                    "aclaraciones": clarifications,
                    "candidatas_ia": fallbacks,
                    "respuestas_seguras": safe_answers,
                    "respuestas_directas_incorrectas": wrong_direct_answers,
                }
                ranking = (
                    candidate["utilidad"],
                    -candidate["respuestas_directas_incorrectas"],
                    candidate["exactitud"],
                    candidate["respuestas_locales"],
                )
                if best_result is None or ranking > best_result["_ranking"]:
                    best_result = {**candidate, "_ranking": ranking}

    assert best_result is not None
    best_result.pop("_ranking")
    best_result["configuracion_actual"] = {
        "umbral_alto": HIGH_CONFIDENCE_THRESHOLD,
        "umbral_medio": MEDIUM_CONFIDENCE_THRESHOLD,
        "margen_ambiguedad": AMBIGUITY_MARGIN,
    }
    return best_result


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
    professional_splits = build_professional_dataset()
    challenge = build_challenge_dataset()
    return {
        "dataset": {name: len(values) for name, values in splits.items()},
        "dataset_profesional": dataset_summary(professional_splits),
        "errores_dataset": validate_professional_dataset(professional_splits),
        "train": evaluate_split(splits["train"]),
        "validation": evaluate_split(splits["validation"]),
        "test": evaluate_split(splits["test"]),
        "challenge": evaluate_split(challenge),
        "calibracion_umbrales": calibrate_thresholds(splits["validation"], challenge),
        "comparacion_modelos": {
            "validation": compare_models(splits["validation"]),
            "test": compare_models(splits["test"]),
            "challenge": compare_models(challenge),
        },
        "nota": (
            "Metricas calculadas sobre dataset profesional balanceado por intencion. "
            "El split challenge contiene preguntas fuera de dominio, ambiguas o que requieren validacion."
        ),
    }
