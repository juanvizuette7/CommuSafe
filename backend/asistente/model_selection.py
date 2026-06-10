"""Entrenamiento y seleccion reproducible de modelos locales para CommuBot.

El modulo compara enfoques ligeros adecuados para el tamano del proyecto:
clasificacion por palabras, centroides TF-IDF, n-gramas de caracteres,
ensambles locales y el motor hibrido de produccion. No usa servicios externos
ni mide la calidad por precision de entrenamiento.
"""

from __future__ import annotations

import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .evaluation import EvaluationExample, build_challenge_dataset, build_dataset
from .local_engine import (
    AMBIGUITY_MARGIN,
    DOMAIN_TERMS,
    ENGINE,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    normalize_text,
    tokenize,
)
from .taxonomy import MAIN_INTENTS


NO_INTENT = "sin_intencion_confiable"


@dataclass(frozen=True)
class RawPrediction:
    intent: str
    confidence: float
    second_intent: str = ""
    second_confidence: float = 0.0
    method: str = ""


@dataclass(frozen=True)
class DecisionPrediction:
    intent: str
    confidence: float
    action: str
    method: str
    second_intent: str = ""
    second_confidence: float = 0.0


@dataclass(frozen=True)
class ModelConfig:
    high_threshold: float
    medium_threshold: float
    ambiguity_margin: float


@dataclass(frozen=True)
class ModelEvaluation:
    total: int
    correctas: int
    precision_micro: float
    recall_micro: float
    f1_micro: float
    cobertura_local: float
    tasa_aclaracion: float
    tasa_respuesta_segura: float
    tasa_uso_ia_estimado: float
    respuestas_directas_incorrectas: int
    latencia_promedio_ms: float
    matriz_confusion: dict[str, dict[str, int]]
    errores: list[dict[str, Any]]


class BaseIntentModel:
    """Contrato minimo para modelos locales entrenables."""

    id = "base"
    label = "Base"
    description = ""
    runtime_decision = False

    def train(self, examples: list[EvaluationExample]) -> None:
        raise NotImplementedError

    def predict_raw(self, text: str, role: str = "RESIDENTE") -> RawPrediction:
        raise NotImplementedError

    def predict_runtime(self, text: str, role: str = "RESIDENTE") -> DecisionPrediction:
        raw = self.predict_raw(text, role)
        return DecisionPrediction(
            intent=raw.intent,
            confidence=raw.confidence,
            action="answer",
            method=raw.method,
            second_intent=raw.second_intent,
            second_confidence=raw.second_confidence,
        )


class KeywordIntentModel(BaseIntentModel):
    id = "keyword_baseline_entrenado"
    label = "Baseline por palabras clave"
    description = "Clasificador simple por solapamiento de tokens aprendidos del train."

    def __init__(self) -> None:
        self.intent_terms: dict[str, Counter[str]] = {}
        self.intent_norms: dict[str, float] = {}

    def train(self, examples: list[EvaluationExample]) -> None:
        counters: dict[str, Counter[str]] = defaultdict(Counter)
        for example in examples:
            counters[example.expected_intent].update(tokenize(example.text))
        self.intent_terms = dict(counters)
        self.intent_norms = {
            intent: math.sqrt(sum(value * value for value in terms.values())) or 1.0
            for intent, terms in self.intent_terms.items()
        }

    def predict_raw(self, text: str, role: str = "RESIDENTE") -> RawPrediction:
        query_tokens = Counter(tokenize(text))
        if not query_tokens:
            return RawPrediction(NO_INTENT, 0.0, method=self.id)
        query_norm = math.sqrt(sum(value * value for value in query_tokens.values())) or 1.0
        scored = []
        for intent, terms in self.intent_terms.items():
            dot = sum(query_tokens[token] * terms.get(token, 0) for token in query_tokens)
            score = dot / (query_norm * self.intent_norms.get(intent, 1.0))
            scored.append((intent, score))
        return _top_prediction(scored, self.id)


class TfidfCentroidIntentModel(BaseIntentModel):
    """Clasificador por centroides TF-IDF entrenado sobre el split train."""

    def __init__(
        self,
        *,
        model_id: str,
        label: str,
        description: str,
        analyzer: Callable[[str], list[str]],
    ) -> None:
        self.id = model_id
        self.label = label
        self.description = description
        self.analyzer = analyzer
        self.idf: dict[str, float] = {}
        self.centroids: dict[str, dict[str, float]] = {}
        self.norms: dict[str, float] = {}

    def train(self, examples: list[EvaluationExample]) -> None:
        docs: list[tuple[str, Counter[str]]] = []
        document_frequency: Counter[str] = Counter()
        for example in examples:
            tokens = Counter(self.analyzer(example.text))
            if not tokens:
                continue
            docs.append((example.expected_intent, tokens))
            for token in tokens:
                document_frequency[token] += 1

        total_docs = max(len(docs), 1)
        self.idf = {
            token: math.log((1 + total_docs) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

        intent_vectors: dict[str, Counter[str]] = defaultdict(Counter)
        intent_counts: Counter[str] = Counter()
        for intent, tokens in docs:
            intent_counts[intent] += 1
            for token, count in tokens.items():
                intent_vectors[intent][token] += count * self.idf.get(token, 1.0)

        self.centroids = {}
        self.norms = {}
        for intent, vector_counter in intent_vectors.items():
            count = max(intent_counts[intent], 1)
            vector = {token: value / count for token, value in vector_counter.items()}
            norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
            self.centroids[intent] = vector
            self.norms[intent] = norm

    def predict_raw(self, text: str, role: str = "RESIDENTE") -> RawPrediction:
        query_vector = self._vectorize(text)
        if not query_vector:
            return RawPrediction(NO_INTENT, 0.0, method=self.id)
        query_norm = math.sqrt(sum(value * value for value in query_vector.values())) or 1.0
        scored = []
        for intent, centroid in self.centroids.items():
            dot = sum(query_vector[token] * centroid.get(token, 0.0) for token in query_vector)
            scored.append((intent, dot / (query_norm * self.norms.get(intent, 1.0))))
        return _top_prediction(scored, self.id)

    def _vectorize(self, text: str) -> dict[str, float]:
        tokens = Counter(self.analyzer(text))
        return {token: count * self.idf.get(token, 1.0) for token, count in tokens.items()}


class HybridCentroidIntentModel(BaseIntentModel):
    """Ensamble de centroides por palabra y por n-gramas de caracteres."""

    def __init__(self, word_weight: float) -> None:
        self.word_weight = word_weight
        self.char_weight = 1.0 - word_weight
        self.id = f"ensamble_word_char_{int(word_weight * 100)}"
        self.label = f"Ensamble TF-IDF palabra/caracter {word_weight:.2f}/{self.char_weight:.2f}"
        self.description = (
            "Combina clasificacion por palabras y n-gramas de caracteres para generalizar "
            "mejor ante preguntas nuevas y errores ortograficos."
        )
        self.word = TfidfCentroidIntentModel(
            model_id="tfidf_palabras_interno",
            label="TF-IDF palabras interno",
            description="",
            analyzer=tokenize,
        )
        self.char = TfidfCentroidIntentModel(
            model_id="tfidf_caracteres_interno",
            label="TF-IDF caracteres interno",
            description="",
            analyzer=char_ngrams,
        )

    def train(self, examples: list[EvaluationExample]) -> None:
        self.word.train(examples)
        self.char.train(examples)

    def predict_raw(self, text: str, role: str = "RESIDENTE") -> RawPrediction:
        word_scores = _scores_by_intent(self.word, text)
        char_scores = _scores_by_intent(self.char, text)
        intents = set(word_scores) | set(char_scores)
        scored = [
            (
                intent,
                self.word_weight * word_scores.get(intent, 0.0)
                + self.char_weight * char_scores.get(intent, 0.0),
            )
            for intent in intents
        ]
        return _top_prediction(scored, self.id)


class ProductionHybridModel(BaseIntentModel):
    id = "hibrido_produccion_kb"
    label = "Hibrido local de produccion"
    description = (
        "Motor activo de CommuSafe: coincidencia exacta, recuperacion por FAQ, "
        "palabras clave, TF-IDF, filtro de dominio, aclaraciones y fallback seguro."
    )
    runtime_decision = True

    def train(self, examples: list[EvaluationExample]) -> None:
        return None

    def predict_raw(self, text: str, role: str = "RESIDENTE") -> RawPrediction:
        result = ENGINE.resolve(text, role)
        return RawPrediction(
            intent=result.get("intent", NO_INTENT),
            confidence=float(result.get("confidence", 0.0) or 0.0),
            method=result.get("method", self.id),
        )

    def predict_runtime(self, text: str, role: str = "RESIDENTE") -> DecisionPrediction:
        result = ENGINE.resolve(text, role)
        return DecisionPrediction(
            intent=result.get("intent", NO_INTENT),
            confidence=float(result.get("confidence", 0.0) or 0.0),
            action=result.get("action", "safe"),
            method=result.get("method", self.id),
        )


def char_ngrams(text: str, min_n: int = 3, max_n: int = 5) -> list[str]:
    normalized = f" {normalize_text(text)} "
    if len(normalized.strip()) < min_n:
        return []
    grams = []
    for n in range(min_n, max_n + 1):
        grams.extend(normalized[index : index + n] for index in range(0, max(len(normalized) - n + 1, 0)))
    return grams


def build_candidate_models() -> list[BaseIntentModel]:
    return [
        KeywordIntentModel(),
        TfidfCentroidIntentModel(
            model_id="tfidf_centroides_palabra",
            label="TF-IDF centroides por palabra",
            description="Clasificador supervisado ligero por similitud a centroides de intencion.",
            analyzer=tokenize,
        ),
        TfidfCentroidIntentModel(
            model_id="tfidf_centroides_caracter",
            label="TF-IDF centroides por caracteres",
            description="Clasificador robusto ante errores ortograficos con n-gramas de caracteres.",
            analyzer=char_ngrams,
        ),
        HybridCentroidIntentModel(word_weight=0.35),
        HybridCentroidIntentModel(word_weight=0.50),
        HybridCentroidIntentModel(word_weight=0.65),
        ProductionHybridModel(),
    ]


def train_compare_select_models(seed: int = 42) -> dict[str, Any]:
    """Entrena, compara y selecciona modelo con evidencia reproducible."""

    splits = build_dataset(seed=seed)
    challenge = build_challenge_dataset()
    train_examples = splits["train"]
    validation_examples = splits["validation"]
    test_examples = splits["test"]
    candidates = build_candidate_models()

    results: dict[str, Any] = {}
    selection_rows = []
    for model in candidates:
        model.train(train_examples)
        config = _active_config(model) if model.runtime_decision else calibrate_model(model, validation_examples, challenge)
        evaluations = {
            "train": evaluate_model(model, train_examples, config),
            "validation": evaluate_model(model, validation_examples, config),
            "test": evaluate_model(model, test_examples, config),
            "challenge": evaluate_model(model, challenge, config),
        }
        score = _generalization_score(evaluations)
        row = {
            "id": model.id,
            "nombre": model.label,
            "descripcion": model.description,
            "configuracion": asdict(config),
            "puntaje_generalizacion": round(score, 4),
            "sobreajuste_train_test": round(
                evaluations["train"].f1_micro - evaluations["test"].f1_micro,
                4,
            ),
            "validation_f1": evaluations["validation"].f1_micro,
            "test_f1": evaluations["test"].f1_micro,
            "challenge_f1": evaluations["challenge"].f1_micro,
            "directas_incorrectas_test": evaluations["test"].respuestas_directas_incorrectas,
        }
        selection_rows.append(row)
        results[model.id] = {
            **row,
            "metricas": {
                split: asdict(evaluation)
                for split, evaluation in evaluations.items()
            },
        }

    selection_rows.sort(
        key=lambda row: (
            row["puntaje_generalizacion"],
            -row["directas_incorrectas_test"],
            row["test_f1"],
            row["challenge_f1"],
        ),
        reverse=True,
    )
    selected = selection_rows[0]
    return {
        "resumen_dataset": {
            "train": len(train_examples),
            "validation": len(validation_examples),
            "test": len(test_examples),
            "challenge": len(challenge),
            "intenciones": len(MAIN_INTENTS),
        },
        "criterio_seleccion": (
            "El modelo se selecciona por un puntaje interno ponderado de validation, test controlado "
            "y challenge de desarrollo, penalizando sobreajuste y respuestas directas incorrectas. "
            "Este puntaje sirve para comparar candidatos, pero no reemplaza el holdout final independiente."
        ),
        "ranking": selection_rows,
        "modelo_seleccionado": selected,
        "modelos": results,
        "analisis_limitaciones": _build_limitations(results[selected["id"]]),
    }


def calibrate_model(
    model: BaseIntentModel,
    validation_examples: list[EvaluationExample],
    challenge_examples: list[EvaluationExample],
) -> ModelConfig:
    """Calibra umbrales usando validation + challenge, nunca test."""

    high_values = [round(value / 100, 2) for value in range(45, 76, 3)]
    medium_values = [round(value / 100, 2) for value in range(18, 52, 3)]
    margin_values = [round(value / 100, 2) for value in range(2, 15, 2)]
    examples = validation_examples + challenge_examples
    precomputed = [
        (example, model.predict_raw(example.text, example.role))
        for example in examples
    ]
    best: tuple[tuple[float, ...], ModelConfig] | None = None

    for high in high_values:
        for medium in medium_values:
            if medium >= high:
                continue
            for margin in margin_values:
                config = ModelConfig(high, medium, margin)
                evaluation = _evaluate_precomputed(precomputed, config)
                utility = (
                    evaluation.f1_micro
                    + evaluation.cobertura_local * 0.22
                    + evaluation.tasa_respuesta_segura * 0.08
                    - evaluation.respuestas_directas_incorrectas * 0.08
                    - abs(evaluation.tasa_uso_ia_estimado - 0.08) * 0.04
                )
                ranking = (
                    utility,
                    -evaluation.respuestas_directas_incorrectas,
                    evaluation.f1_micro,
                    evaluation.cobertura_local,
                )
                if best is None or ranking > best[0]:
                    best = (ranking, config)

    assert best is not None
    return best[1]


def evaluate_model(
    model: BaseIntentModel,
    examples: list[EvaluationExample],
    config: ModelConfig,
) -> ModelEvaluation:
    total = len(examples)
    correct = 0
    local_answers = 0
    clarifications = 0
    safe_answers = 0
    generative_candidates = 0
    wrong_direct = 0
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    errors: list[dict[str, Any]] = []
    latencies = []

    for example in examples:
        started = time.perf_counter()
        if model.runtime_decision:
            decision = model.predict_runtime(example.text, example.role)
        else:
            decision = _apply_policy(model.predict_raw(example.text, example.role), example.text, config)
        latencies.append((time.perf_counter() - started) * 1000)
        is_correct = _is_operationally_correct(example, decision)
        correct += int(is_correct)
        local_answers += int(decision.action == "answer")
        clarifications += int(decision.action == "clarify")
        safe_answers += int(decision.action == "safe")
        generative_candidates += int(decision.action == "fallback_allowed")
        wrong_direct += int(decision.action == "answer" and not is_correct)
        confusion[example.expected_intent][decision.intent] += 1
        if not is_correct:
            errors.append(
                {
                    "texto": example.text,
                    "esperada": example.expected_intent,
                    "predicha": decision.intent,
                    "accion": decision.action,
                    "confianza": round(decision.confidence, 4),
                    "segunda": decision.second_intent,
                    "confianza_segunda": round(decision.second_confidence, 4),
                    "metodo": decision.method,
                }
            )

    accuracy = correct / total if total else 0.0
    return ModelEvaluation(
        total=total,
        correctas=correct,
        precision_micro=round(accuracy, 4),
        recall_micro=round(accuracy, 4),
        f1_micro=round(accuracy, 4),
        cobertura_local=round(local_answers / total, 4) if total else 0.0,
        tasa_aclaracion=round(clarifications / total, 4) if total else 0.0,
        tasa_respuesta_segura=round(safe_answers / total, 4) if total else 0.0,
        tasa_uso_ia_estimado=round(generative_candidates / total, 4) if total else 0.0,
        respuestas_directas_incorrectas=wrong_direct,
        latencia_promedio_ms=round(sum(latencies) / total, 4) if total else 0.0,
        matriz_confusion={
            expected: dict(predicted_counter)
            for expected, predicted_counter in sorted(confusion.items())
        },
        errores=errors[:30],
    )


def _evaluate_precomputed(
    predictions: list[tuple[EvaluationExample, RawPrediction]],
    config: ModelConfig,
) -> ModelEvaluation:
    total = len(predictions)
    correct = 0
    local_answers = 0
    clarifications = 0
    safe_answers = 0
    generative_candidates = 0
    wrong_direct = 0
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    errors: list[dict[str, Any]] = []

    for example, raw in predictions:
        decision = _apply_policy(raw, example.text, config)
        is_correct = _is_operationally_correct(example, decision)
        correct += int(is_correct)
        local_answers += int(decision.action == "answer")
        clarifications += int(decision.action == "clarify")
        safe_answers += int(decision.action == "safe")
        generative_candidates += int(decision.action == "fallback_allowed")
        wrong_direct += int(decision.action == "answer" and not is_correct)
        confusion[example.expected_intent][decision.intent] += 1
        if not is_correct:
            errors.append(
                {
                    "texto": example.text,
                    "esperada": example.expected_intent,
                    "predicha": decision.intent,
                    "accion": decision.action,
                    "confianza": round(decision.confidence, 4),
                    "segunda": decision.second_intent,
                    "confianza_segunda": round(decision.second_confidence, 4),
                    "metodo": decision.method,
                }
            )

    accuracy = correct / total if total else 0.0
    return ModelEvaluation(
        total=total,
        correctas=correct,
        precision_micro=round(accuracy, 4),
        recall_micro=round(accuracy, 4),
        f1_micro=round(accuracy, 4),
        cobertura_local=round(local_answers / total, 4) if total else 0.0,
        tasa_aclaracion=round(clarifications / total, 4) if total else 0.0,
        tasa_respuesta_segura=round(safe_answers / total, 4) if total else 0.0,
        tasa_uso_ia_estimado=round(generative_candidates / total, 4) if total else 0.0,
        respuestas_directas_incorrectas=wrong_direct,
        latencia_promedio_ms=0.0,
        matriz_confusion={
            expected: dict(predicted_counter)
            for expected, predicted_counter in sorted(confusion.items())
        },
        errores=errors[:30],
    )


def export_model_selection_report(payload: dict[str, Any], json_path: str | Path | None = None) -> None:
    if not json_path:
        return
    path = Path(json_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_model_selection_markdown(payload: dict[str, Any], markdown_path: str | Path | None = None) -> None:
    if not markdown_path:
        return
    path = Path(markdown_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = payload["modelo_seleccionado"]
    lines = [
        "# Seleccion de modelo local del asistente CommuSafe",
        "",
        "Este reporte es generado por `python manage.py evaluar_modelos_asistente`.",
        "",
        "## Dataset",
        "",
        "| Split | Ejemplos |",
        "|---|---:|",
    ]
    for split, amount in payload["resumen_dataset"].items():
        lines.append(f"| {split} | {amount} |")
    lines.extend(
        [
            "",
            "## Criterio de seleccion",
            "",
            payload["criterio_seleccion"],
            "",
            "## Ranking",
            "",
            "| Modelo | Validation F1 | Test F1 | Challenge desarrollo | Puntaje interno | Directas incorrectas test |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["ranking"]:
        lines.append(
            "| {nombre} | {validation_f1:.4f} | {test_f1:.4f} | {challenge_f1:.4f} | "
            "{puntaje_generalizacion:.4f} | {directas_incorrectas_test} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Modelo seleccionado",
            "",
            f"- **Modelo:** {selected['nombre']}",
            f"- **ID:** `{selected['id']}`",
            f"- **Puntaje de comparacion interna:** {selected['puntaje_generalizacion']}",
            f"- **Configuracion:** `{selected['configuracion']}`",
            "",
            "## Limitaciones observadas",
            "",
        ]
    )
    for item in payload["analisis_limitaciones"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _active_config(model: BaseIntentModel) -> ModelConfig:
    if model.runtime_decision:
        return ModelConfig(HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD, AMBIGUITY_MARGIN)
    return ModelConfig(0.5, 0.25, 0.05)


def _apply_policy(raw: RawPrediction, text: str, config: ModelConfig) -> DecisionPrediction:
    query_tokens = set(tokenize(text))
    if query_tokens and not (query_tokens & DOMAIN_TERMS):
        return DecisionPrediction(NO_INTENT, 0.0, "safe", "fuera_de_dominio")
    if raw.confidence >= config.high_threshold and (
        raw.confidence - raw.second_confidence
    ) >= config.ambiguity_margin:
        action = "answer"
    elif raw.confidence >= config.medium_threshold:
        action = "clarify"
    elif query_tokens:
        action = "fallback_allowed"
    else:
        action = "safe"
    return DecisionPrediction(
        raw.intent,
        raw.confidence,
        action,
        raw.method,
        raw.second_intent,
        raw.second_confidence,
    )


def _is_operationally_correct(example: EvaluationExample, decision: DecisionPrediction) -> bool:
    if example.expected_intent == NO_INTENT:
        return decision.action in {"safe", "fallback_allowed"} or decision.intent == NO_INTENT
    return decision.intent == example.expected_intent and decision.action in {"answer", "clarify"}


def _generalization_score(evaluations: dict[str, ModelEvaluation]) -> float:
    train = evaluations["train"]
    validation = evaluations["validation"]
    test = evaluations["test"]
    challenge = evaluations["challenge"]
    overfit = max(0.0, train.f1_micro - test.f1_micro)
    wrong_direct_penalty = test.respuestas_directas_incorrectas * 0.03
    return (
        validation.f1_micro * 0.30
        + test.f1_micro * 0.45
        + challenge.f1_micro * 0.25
        - overfit * 0.15
        - wrong_direct_penalty
    )


def _top_prediction(scored: Iterable[tuple[str, float]], method: str) -> RawPrediction:
    ordered = sorted(scored, key=lambda item: item[1], reverse=True)
    if not ordered:
        return RawPrediction(NO_INTENT, 0.0, method=method)
    best_intent, best_score = ordered[0]
    second_intent, second_score = ordered[1] if len(ordered) > 1 else ("", 0.0)
    return RawPrediction(
        best_intent,
        max(0.0, min(1.0, best_score)),
        second_intent,
        max(0.0, min(1.0, second_score)),
        method,
    )


def _scores_by_intent(model: TfidfCentroidIntentModel, text: str) -> dict[str, float]:
    query_vector = model._vectorize(text)  # noqa: SLF001 - comparacion interna reproducible.
    if not query_vector:
        return {}
    query_norm = math.sqrt(sum(value * value for value in query_vector.values())) or 1.0
    scores = {}
    for intent, centroid in model.centroids.items():
        dot = sum(query_vector[token] * centroid.get(token, 0.0) for token in query_vector)
        scores[intent] = dot / (query_norm * model.norms.get(intent, 1.0))
    return scores


def _build_limitations(selected_payload: dict[str, Any]) -> list[str]:
    test_errors = selected_payload["metricas"]["test"]["errores"]
    challenge_errors = selected_payload["metricas"]["challenge"]["errores"]
    limitations = [
        "El dataset es controlado y debe complementarse con preguntas reales de usuarios despues de la sustentacion.",
        "El split challenge muestra que preguntas muy ambiguas o fuera de dominio deben resolverse con aclaracion o respuesta segura, no con respuesta directa.",
        "No se uso un modelo neuronal externo para clasificacion local porque el tamano del dataset no justifica una dependencia pesada en produccion.",
    ]
    if test_errors:
        limitations.append(
            f"En test quedaron {len(test_errors)} errores operacionales revisables; los primeros casos quedan en el JSON de evidencia."
        )
    if challenge_errors:
        limitations.append(
            f"En challenge quedaron {len(challenge_errors)} errores o rechazos seguros esperados por ambiguedad o falta de informacion verificable."
        )
    return limitations
