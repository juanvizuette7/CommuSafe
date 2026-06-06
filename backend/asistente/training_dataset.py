"""Dataset profesional de entrenamiento para comprension local de CommuBot."""

from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .local_engine import normalize_text
from .local_knowledge import FAQEntry, FAQ_ENTRIES
from .taxonomy import MAIN_INTENTS


SPLIT_RATIOS = {"train": 4, "validation": 1, "test": 1}
REQUIRED_STYLES = {"formal", "informal", "corta", "larga", "error_ortografico", "no_tecnico"}
EXAMPLES_PER_STYLE_PER_INTENT = sum(SPLIT_RATIOS.values())
EXAMPLES_PER_INTENT = len(REQUIRED_STYLES) * EXAMPLES_PER_STYLE_PER_INTENT


@dataclass(frozen=True)
class TrainingExample:
    text: str
    intent: str
    subintent: str
    category: str
    role: str
    entry_id: str
    style: str
    split: str
    verified: bool
    requires_admin_validation: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _without_question_marks(text: str) -> str:
    return _clean(text.strip("¿? "))


def _question_lower(entry: FAQEntry) -> str:
    return _without_question_marks(entry.question).lower()


def _keyword_phrase(entry: FAQEntry, amount: int = 3) -> str:
    return " ".join(entry.keywords[:amount])


def _typo_variant(text: str) -> str:
    replacements = {
        "como": "komo",
        "que": "q",
        "administracion": "adminstracion",
        "contrasena": "contrseña",
        "incidente": "insidente",
        "notificacion": "notificasion",
        "parqueadero": "parkiadero",
        "seguridad": "segurida",
        "telefono": "cel",
        "vehiculo": "veiculo",
    }
    normalized = normalize_text(text)
    tokens = normalized.split()
    changed = []
    replaced = False
    for token in tokens:
        if token in replacements and not replaced:
            changed.append(replacements[token])
            replaced = True
        else:
            changed.append(token)
    if not replaced and tokens:
        changed[0] = tokens[0][:-1] if len(tokens[0]) > 4 else f"{tokens[0]}?"
    return _clean(" ".join(changed))


def _candidate_texts(entry: FAQEntry) -> list[tuple[str, str]]:
    base_question = _without_question_marks(entry.question)
    question_lower = _question_lower(entry)
    keywords = _keyword_phrase(entry)
    first_keyword = entry.keywords[0] if entry.keywords else entry.intent
    second_keyword = entry.keywords[1] if len(entry.keywords) > 1 else entry.category

    candidates = [
        ("formal", entry.question),
        ("informal", f"Me ayudas con esto: {question_lower}?"),
        ("corta", keywords),
        (
            "larga",
            f"Tengo una situacion relacionada con {keywords}; necesito saber {question_lower} dentro de CommuSafe.",
        ),
        ("error_ortografico", _typo_variant(question_lower)),
        ("no_tecnico", f"No entiendo lo de {first_keyword} y {second_keyword}, que hago?"),
    ]

    variation_styles = ["informal", "corta", "larga", "no_tecnico", "formal"]
    for index, variation in enumerate(entry.variations):
        candidates.append((variation_styles[index % len(variation_styles)], variation))

    candidates.append(("formal", f"Necesito orientacion sobre {base_question.lower()}."))
    candidates.append(("informal", f"Ey, tengo duda con {first_keyword}, {question_lower}?"))
    candidates.append(("error_ortografico", _typo_variant(f"{first_keyword} {second_keyword} {question_lower}")))

    unique: dict[str, tuple[str, str]] = {}
    for style, text in candidates:
        text = _clean(text)
        normalized = normalize_text(text)
        if text and normalized not in unique:
            unique[normalized] = (style, text)
    return list(unique.values())


def _select_intent_candidates(
    intent_id: str,
    entries: list[FAQEntry],
    seed: int,
) -> list[tuple[str, str, FAQEntry]]:
    """Selecciona ejemplos variados y balanceados para una intencion principal."""

    selected: list[tuple[str, str, FAQEntry]] = []
    styles = sorted(REQUIRED_STYLES)
    for style_index, style in enumerate(styles):
        ordered_entries = entries[style_index % len(entries):] + entries[:style_index % len(entries)]
        for example_index in range(EXAMPLES_PER_STYLE_PER_INTENT):
            entry = ordered_entries[example_index % len(ordered_entries)]
            options = [
                text
                for candidate_style, text in _candidate_texts(entry)
                if candidate_style == style
            ]
            if not options:
                options = [entry.question]
            rng = random.Random(f"{seed}:{intent_id}:{style}:{entry.id}:{example_index}")
            selected.append((style, rng.choice(options), entry))
    return selected


def build_professional_dataset(seed: int = 42) -> dict[str, list[TrainingExample]]:
    """Construye splits estratificados, balanceados y sin frases repetidas."""

    splits: dict[str, list[TrainingExample]] = {"train": [], "validation": [], "test": []}
    used_global_texts: set[str] = set()

    entries_by_id = {entry.id: entry for entry in FAQ_ENTRIES}
    for main_intent in MAIN_INTENTS:
        entries = [entries_by_id[faq_id] for faq_id in main_intent.faq_ids]
        selected = _select_intent_candidates(main_intent.id, entries, seed)
        split_plan = (
            ["train"] * SPLIT_RATIOS["train"]
            + ["validation"] * SPLIT_RATIOS["validation"]
            + ["test"] * SPLIT_RATIOS["test"]
        )

        for style_index, style in enumerate(sorted(REQUIRED_STYLES)):
            style_examples = [item for item in selected if item[0] == style]
            for split, (_, text, entry) in zip(split_plan, style_examples, strict=True):
                role = entry.allowed_roles[0]
                text = _make_global_unique(text, entry, used_global_texts)
                splits[split].append(
                    TrainingExample(
                        text=text,
                        intent=main_intent.id,
                        subintent=entry.intent,
                        category=entry.category,
                        role=role,
                        entry_id=entry.id,
                        style=style,
                        split=split,
                        verified=entry.verified,
                        requires_admin_validation=not entry.verified,
                    )
                )

    for values in splits.values():
        values.sort(key=lambda item: (item.category, item.intent, item.style, normalize_text(item.text)))

    return splits


def _make_global_unique(text: str, entry: FAQEntry, used_global_texts: set[str]) -> str:
    """Evita que una misma frase quede en dos intenciones o particiones."""

    candidates = [
        text,
        f"{text} en {entry.category.replace('_', ' ')}",
        f"{text} sobre {entry.keywords[0] if entry.keywords else entry.intent}",
        f"{text} para {entry.main_intent.replace('_', ' ')}",
        f"{text} relacionado con {entry.question.lower().strip('¿? ')}",
    ]
    for candidate in candidates:
        normalized = normalize_text(candidate)
        if normalized not in used_global_texts:
            used_global_texts.add(normalized)
            return candidate

    suffix = 1
    while True:
        candidate = f"{text} consulta adicional {suffix} sobre {entry.keywords[0]}"
        normalized = normalize_text(candidate)
        if normalized not in used_global_texts:
            used_global_texts.add(normalized)
            return candidate
        suffix += 1


def dataset_summary(splits: dict[str, list[TrainingExample]]) -> dict[str, Any]:
    """Resume balance, estilos y cobertura del dataset."""

    all_examples = [example for examples in splits.values() for example in examples]
    intents = {example.intent for example in all_examples}
    by_split = {name: len(examples) for name, examples in splits.items()}
    by_style = Counter(example.style for example in all_examples)
    by_split_style = {
        split: dict(sorted(Counter(example.style for example in examples).items()))
        for split, examples in splits.items()
    }
    by_category = Counter(example.category for example in all_examples)
    examples_per_intent = Counter(example.intent for example in all_examples)
    represented_faq = {example.entry_id for example in all_examples}
    return {
        "total": len(all_examples),
        "splits": by_split,
        "intenciones": len(intents),
        "categorias": len(by_category),
        "estilos": dict(sorted(by_style.items())),
        "estilos_por_split": by_split_style,
        "categorias_detalle": dict(sorted(by_category.items())),
        "faq_representadas": len(represented_faq),
        "faq_totales": len(FAQ_ENTRIES),
        "min_ejemplos_por_intencion": min(examples_per_intent.values()) if examples_per_intent else 0,
        "max_ejemplos_por_intencion": max(examples_per_intent.values()) if examples_per_intent else 0,
        "balanceado_por_intencion": len(set(examples_per_intent.values())) == 1,
    }


def validate_professional_dataset(splits: dict[str, list[TrainingExample]]) -> list[str]:
    """Detecta fugas entre particiones, duplicados, desbalance y ambiguedad basica."""

    errors: list[str] = []
    all_examples = [example for examples in splits.values() for example in examples]
    normalized_to_examples: dict[str, list[TrainingExample]] = defaultdict(list)
    intent_to_styles: dict[str, set[str]] = defaultdict(set)
    intent_to_splits: dict[str, Counter[str]] = defaultdict(Counter)
    text_to_intents: dict[str, set[str]] = defaultdict(set)
    split_to_styles: dict[str, Counter[str]] = defaultdict(Counter)

    for example in all_examples:
        normalized = normalize_text(example.text)
        normalized_to_examples[normalized].append(example)
        intent_to_styles[example.intent].add(example.style)
        intent_to_splits[example.intent][example.split] += 1
        text_to_intents[normalized].add(example.intent)
        split_to_styles[example.split][example.style] += 1

    for normalized, examples in normalized_to_examples.items():
        split_names = {example.split for example in examples}
        if len(examples) > 1:
            errors.append(
                f"Texto duplicado en dataset: '{normalized}' aparece en {sorted(split_names)}."
            )

    for normalized, intents in text_to_intents.items():
        if len(intents) > 1:
            errors.append(f"Texto ambiguo '{normalized}' asignado a intenciones {sorted(intents)}.")

    for intent, split_counts in intent_to_splits.items():
        expected_train = len(REQUIRED_STYLES) * SPLIT_RATIOS["train"]
        expected_validation = len(REQUIRED_STYLES) * SPLIT_RATIOS["validation"]
        expected_test = len(REQUIRED_STYLES) * SPLIT_RATIOS["test"]
        if split_counts["train"] != expected_train:
            errors.append(f"{intent}: cantidad train inesperada ({split_counts['train']}).")
        if split_counts["validation"] != expected_validation:
            errors.append(f"{intent}: cantidad validation inesperada ({split_counts['validation']}).")
        if split_counts["test"] != expected_test:
            errors.append(f"{intent}: cantidad test inesperada ({split_counts['test']}).")
        missing_styles = REQUIRED_STYLES - intent_to_styles[intent]
        if missing_styles:
            errors.append(f"{intent}: faltan estilos {sorted(missing_styles)}.")

    total_intents = len(intent_to_splits)
    for style in REQUIRED_STYLES:
        expected_train = total_intents * SPLIT_RATIOS["train"]
        expected_validation = total_intents * SPLIT_RATIOS["validation"]
        expected_test = total_intents * SPLIT_RATIOS["test"]
        if split_to_styles["validation"][style] != expected_validation:
            errors.append(
                f"validation: estilo {style} tiene {split_to_styles['validation'][style]}, "
                f"esperado {expected_validation}."
            )
        if split_to_styles["test"][style] != expected_test:
            errors.append(
                f"test: estilo {style} tiene {split_to_styles['test'][style]}, "
                f"esperado {expected_test}."
            )
        if split_to_styles["train"][style] != expected_train:
            errors.append(
                f"train: estilo {style} tiene {split_to_styles['train'][style]}, "
                f"esperado {expected_train}."
            )

    represented_faq = {example.entry_id for example in all_examples}
    missing_faq = sorted({entry.id for entry in FAQ_ENTRIES} - represented_faq)
    if missing_faq:
        errors.append(f"FAQ sin representacion en dataset: {missing_faq}.")

    return errors
