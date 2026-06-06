"""Dataset profesional de entrenamiento para comprension local de CommuBot."""

from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .local_engine import normalize_text
from .local_knowledge import FAQEntry, FAQ_ENTRIES


SPLIT_RATIOS = {"train": 4, "validation": 1, "test": 1}
EXAMPLES_PER_INTENT = sum(SPLIT_RATIOS.values())
REQUIRED_STYLES = {"formal", "informal", "corta", "larga", "error_ortografico", "no_tecnico"}


@dataclass(frozen=True)
class TrainingExample:
    text: str
    intent: str
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


def _select_balanced_candidates(entry: FAQEntry, seed: int) -> list[tuple[str, str]]:
    rng = random.Random(f"{seed}:{entry.id}")
    candidates = _candidate_texts(entry)
    by_style: dict[str, list[str]] = defaultdict(list)
    for style, text in candidates:
        by_style[style].append(text)

    selected: list[tuple[str, str]] = []
    used = set()
    for style in sorted(REQUIRED_STYLES):
        options = by_style.get(style, [])
        if not options:
            continue
        text = rng.choice(options)
        normalized = normalize_text(text)
        if normalized not in used:
            selected.append((style, text))
            used.add(normalized)

    remaining = candidates[:]
    rng.shuffle(remaining)
    for style, text in remaining:
        if len(selected) >= EXAMPLES_PER_INTENT:
            break
        normalized = normalize_text(text)
        if normalized not in used:
            selected.append((style, text))
            used.add(normalized)

    while len(selected) < EXAMPLES_PER_INTENT:
        style = "no_tecnico"
        text = f"Tengo una duda sobre {_keyword_phrase(entry)} en CommuSafe {len(selected) + 1}"
        normalized = normalize_text(text)
        if normalized not in used:
            selected.append((style, text))
            used.add(normalized)

    return selected[:EXAMPLES_PER_INTENT]


def build_professional_dataset(seed: int = 42) -> dict[str, list[TrainingExample]]:
    """Construye splits estratificados, balanceados y sin frases repetidas."""

    splits: dict[str, list[TrainingExample]] = {"train": [], "validation": [], "test": []}
    used_global_texts: set[str] = set()

    styles = sorted(REQUIRED_STYLES)

    for entry_index, entry in enumerate(FAQ_ENTRIES):
        selected = _select_balanced_candidates(entry, seed)
        selected_by_style = {style: text for style, text in selected}
        role = entry.allowed_roles[0]
        validation_style = styles[entry_index % len(styles)]
        test_style = styles[(entry_index + 1) % len(styles)]
        train_styles = [style for style in styles if style not in {validation_style, test_style}]
        split_items = (
            [("train", style, selected_by_style[style]) for style in train_styles]
            + [("validation", validation_style, selected_by_style[validation_style])]
            + [("test", test_style, selected_by_style[test_style])]
        )

        for split, style, text in split_items:
            text = _make_global_unique(text, entry, used_global_texts)
            splits[split].append(
                TrainingExample(
                    text=text,
                    intent=entry.intent,
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
        f"{text} para {entry.intent.replace('_', ' ')}",
    ]
    for candidate in candidates:
        normalized = normalize_text(candidate)
        if normalized not in used_global_texts:
            used_global_texts.add(normalized)
            return candidate

    suffix = 1
    while True:
        candidate = f"{text} caso {entry.id} {suffix}"
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
    return {
        "total": len(all_examples),
        "splits": by_split,
        "intenciones": len(intents),
        "categorias": len(by_category),
        "estilos": dict(sorted(by_style.items())),
        "estilos_por_split": by_split_style,
        "categorias_detalle": dict(sorted(by_category.items())),
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
        if split_counts["train"] != SPLIT_RATIOS["train"]:
            errors.append(f"{intent}: cantidad train inesperada ({split_counts['train']}).")
        if split_counts["validation"] != SPLIT_RATIOS["validation"]:
            errors.append(f"{intent}: cantidad validation inesperada ({split_counts['validation']}).")
        if split_counts["test"] != SPLIT_RATIOS["test"]:
            errors.append(f"{intent}: cantidad test inesperada ({split_counts['test']}).")
        missing_styles = REQUIRED_STYLES - intent_to_styles[intent]
        if missing_styles:
            errors.append(f"{intent}: faltan estilos {sorted(missing_styles)}.")

    total_intents = len(intent_to_splits)
    if total_intents and total_intents % len(REQUIRED_STYLES) == 0:
        expected_holdout = total_intents // len(REQUIRED_STYLES)
        expected_train = total_intents - (expected_holdout * 2)
        for style in REQUIRED_STYLES:
            if split_to_styles["validation"][style] != expected_holdout:
                errors.append(
                    f"validation: estilo {style} tiene {split_to_styles['validation'][style]}, "
                    f"esperado {expected_holdout}."
                )
            if split_to_styles["test"][style] != expected_holdout:
                errors.append(
                    f"test: estilo {style} tiene {split_to_styles['test'][style]}, "
                    f"esperado {expected_holdout}."
                )
            if split_to_styles["train"][style] != expected_train:
                errors.append(
                    f"train: estilo {style} tiene {split_to_styles['train'][style]}, "
                    f"esperado {expected_train}."
                )

    return errors
