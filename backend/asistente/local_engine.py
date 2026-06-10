"""Motor local de recuperacion e intenciones para CommuBot.

No depende de servicios externos. Combina coincidencia exacta, palabras clave y
similitud TF-IDF ligera con clasificacion de intencion para responder preguntas
frecuentes sin consumir IA generativa. El motor es stateless para usuarios y
seguro para concurrencia.
"""

from __future__ import annotations

import math
import re
import time
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
from threading import RLock
from typing import Any

from .knowledge_repository import ENTRADAS_ESTATICAS_CONTROLADAS, obtener_snapshot_conocimiento
from .local_knowledge import FAQEntry


HIGH_CONFIDENCE_THRESHOLD = 0.52
MEDIUM_CONFIDENCE_THRESHOLD = 0.28
AMBIGUITY_MARGIN = 0.04
MAX_OPTIONS = 3
TOKEN_RE = re.compile(r"[a-z0-9]+")
COMMON_TOKEN_CORRECTIONS = {
    "autoricen": "autorizar",
    "adminstracion": "administracion",
    "contrsea": "contrasena",
    "contrsena": "contrasena",
    "insidente": "incidente",
    "incidnte": "incidente",
    "komo": "como",
    "notificasion": "notificacion",
    "notificasiones": "notificaciones",
    "parkiadero": "parqueadero",
    "report": "reporte",
    "segurida": "seguridad",
    "veiculo": "vehiculo",
    "yegan": "llegan",
}
STOPWORDS = {
    "a",
    "al",
    "algo",
    "como",
    "con",
    "cual",
    "cuando",
    "de",
    "del",
    "donde",
    "el",
    "en",
    "es",
    "eso",
    "esta",
    "este",
    "hacer",
    "hago",
    "hay",
    "la",
    "las",
    "le",
    "lo",
    "los",
    "me",
    "mi",
    "para",
    "pero",
    "por",
    "puedo",
    "que",
    "se",
    "si",
    "un",
    "una",
    "y",
}
DOMAIN_TERMS = {
    "acceso",
    "administracion",
    "administrador",
    "administrativo",
    "ajuste",
    "ajustes",
    "alerta",
    "app",
    "area",
    "areas",
    "apartamento",
    "asistente",
    "aviso",
    "basura",
    "badge",
    "camara",
    "campana",
    "carro",
    "caso",
    "cartera",
    "cel",
    "celular",
    "cerradura",
    "chat",
    "citofono",
    "commubot",
    "commusafe",
    "comun",
    "comunes",
    "comunicado",
    "conjunto",
    "convivencia",
    "correo",
    "corredor",
    "cuenta",
    "cuota",
    "dashboard",
    "dano",
    "datos",
    "dialogo",
    "domiciliario",
    "emergencia",
    "entrada",
    "evidencia",
    "foto",
    "gas",
    "historial",
    "horario",
    "horarios",
    "humo",
    "incidente",
    "incendio",
    "ingreso",
    "limpieza",
    "luz",
    "logout",
    "luminaria",
    "mantenimiento",
    "mascota",
    "norma",
    "normas",
    "notificacion",
    "oficina",
    "parqueadero",
    "pagar",
    "pelea",
    "perro",
    "paz",
    "perfil",
    "porteria",
    "puerta",
    "poste",
    "proveedor",
    "push",
    "recibo",
    "recibos",
    "reporte",
    "residente",
    "remansos",
    "rol",
    "roles",
    "ruido",
    "sabado",
    "sabados",
    "salvo",
    "seguridad",
    "salida",
    "sesion",
    "sistema",
    "telefono",
    "torre",
    "usuario",
    "vehiculo",
    "vecino",
    "vigilancia",
    "vigilante",
    "visitante",
    "urgente",
    "zona",
}


def normalize_text(text: str) -> str:
    """Normaliza texto para comparaciones robustas ante tildes y puntuacion."""

    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [COMMON_TOKEN_CORRECTIONS.get(token, token) for token in text.split()]
    return re.sub(r"\s+", " ", " ".join(tokens)).strip()


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    tokens = []
    for token in TOKEN_RE.findall(normalized):
        if token in STOPWORDS or len(token) <= 1:
            continue
        tokens.append(token)
        if len(token) > 7 and token.endswith("ciones"):
            tokens.append(f"{token[:-6]}cion")
        if len(token) > 4 and token.endswith("s"):
            tokens.append(token[:-1])
    return tokens


class LocalAssistantEngine:
    """Indice en memoria para resolver preguntas frecuentes."""

    def __init__(self, entries: tuple[FAQEntry, ...] = ENTRADAS_ESTATICAS_CONTROLADAS):
        self.entries = entries
        self._entry_by_id = {entry.id: entry for entry in entries}
        self._exact_index: dict[str, list[FAQEntry]] = {}
        self._entry_tokens: dict[str, Counter[str]] = {}
        self._entry_keywords: dict[str, set[str]] = {}
        self._intent_keywords: dict[str, set[str]] = {}
        self._idf: dict[str, float] = {}
        self._vectors: dict[str, dict[str, float]] = {}
        self._norms: dict[str, float] = {}
        self._intent_vectors: dict[str, dict[str, float]] = {}
        self._intent_norms: dict[str, float] = {}
        self._build_index()

    def _build_index(self) -> None:
        document_frequency: Counter[str] = Counter()
        raw_documents: dict[str, Counter[str]] = {}
        raw_intent_documents: dict[str, Counter[str]] = defaultdict(Counter)
        intent_keywords: dict[str, set[str]] = defaultdict(set)

        for entry in self.entries:
            searchable_chunks = [normalize_text(text) for text in entry.searchable_texts()]
            for chunk in searchable_chunks:
                if chunk:
                    entries = self._exact_index.setdefault(chunk, [])
                    if entry.id not in {indexed.id for indexed in entries}:
                        entries.append(entry)

            tokens = Counter(tokenize(" ".join(searchable_chunks)))
            raw_documents[entry.id] = tokens
            self._entry_tokens[entry.id] = tokens
            self._entry_keywords[entry.id] = set(tokenize(" ".join(entry.keywords)))
            raw_intent_documents[entry.main_intent].update(tokens)
            intent_keywords[entry.main_intent].update(self._entry_keywords[entry.id])
            for token in tokens:
                document_frequency[token] += 1

        total_docs = max(len(raw_documents), 1)
        self._idf = {
            token: math.log((1 + total_docs) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

        for entry_id, tokens in raw_documents.items():
            vector = {token: count * self._idf.get(token, 1.0) for token, count in tokens.items()}
            norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
            self._vectors[entry_id] = vector
            self._norms[entry_id] = norm
        for intent_id, tokens in raw_intent_documents.items():
            vector = {token: count * self._idf.get(token, 1.0) for token, count in tokens.items()}
            norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
            self._intent_vectors[intent_id] = vector
            self._intent_norms[intent_id] = norm
        self._intent_keywords = dict(intent_keywords)

    def resolve(self, message: str, role: str = "RESIDENTE") -> dict[str, Any]:
        started = time.perf_counter()
        role = (role or "RESIDENTE").upper()
        normalized = normalize_text(message)
        if not normalized:
            return self._safe_response(started, reason="mensaje_vacio")

        exact_entries = [
            entry
            for entry in self._exact_index.get(normalized, [])
            if self._role_allowed(entry, role)
        ]
        if len(exact_entries) == 1:
            exact_entry = exact_entries[0]
            return self._answer_payload(
                exact_entry,
                confidence=1.0,
                method="coincidencia_exacta",
                mode="local",
                started=started,
            )
        if len(exact_entries) > 1:
            return self._exact_ambiguity_payload(exact_entries, started)

        business_entry = self._business_rule_entry(normalized, role)
        if business_entry:
            return self._answer_payload(
                business_entry,
                confidence=0.96,
                method="regla_negocio",
                mode="local",
                started=started,
                score_parts={"regla": 1.0},
            )

        query_tokens = set(tokenize(normalized))
        if query_tokens and not (query_tokens & DOMAIN_TERMS):
            return self._safe_response(started, reason="fuera_de_dominio")

        candidates = self._score_candidates(normalized, role)
        if not candidates:
            return self._safe_response(started, reason="sin_candidatos")

        best = candidates[0]
        second = candidates[1] if len(candidates) > 1 else None
        entry = best["entry"]
        confidence = best["confidence"]

        if confidence >= HIGH_CONFIDENCE_THRESHOLD and not self._is_ambiguous(best, second):
            return self._answer_payload(
                entry,
                confidence=confidence,
                method=best["method"],
                mode="local" if best["method"] == "palabras_clave" else "semantica",
                started=started,
                score_parts=best["score_parts"],
            )

        if confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
            options = self._clarification_options(candidates)
            return {
                "action": "clarify",
                "respuesta": self._build_clarification(options),
                "mode": "aclaracion",
                "provider": "local",
                "model": "commusafe-local-hybrid-v3",
                "confidence": round(confidence, 4),
                "intent": entry.main_intent,
                "subintent": entry.intent,
                "entry_id": entry.id,
                "category": entry.category,
                "method": "aclaracion_por_confianza_media",
                "verified": entry.verified,
                "verification_status": entry.verification_status,
                "validity_status": entry.validity_status,
                "valid_from": entry.valid_from,
                "valid_until": entry.valid_until,
                "requires_validation": not entry.verified,
                "options": options,
                "latency_ms": self._elapsed_ms(started),
            }

        return {
            "action": "fallback_allowed",
            "respuesta": "",
            "mode": "baja_confianza",
            "provider": "local",
            "model": "commusafe-local-hybrid-v3",
            "confidence": round(confidence, 4),
            "intent": entry.main_intent,
            "subintent": entry.intent,
            "entry_id": entry.id,
            "category": entry.category,
            "method": best["method"],
            "verified": entry.verified,
            "verification_status": entry.verification_status,
            "validity_status": entry.validity_status,
            "valid_from": entry.valid_from,
            "valid_until": entry.valid_until,
            "requires_validation": not entry.verified,
            "options": [],
            "latency_ms": self._elapsed_ms(started),
        }

    def _score_candidates(self, normalized: str, role: str) -> list[dict[str, Any]]:
        query_tokens = Counter(tokenize(normalized))
        if not query_tokens:
            return []

        query_vector = {token: count * self._idf.get(token, 1.0) for token, count in query_tokens.items()}
        query_norm = math.sqrt(sum(value * value for value in query_vector.values())) or 1.0
        query_token_set = set(query_tokens)
        intent_scores = self._classify_intents(query_vector, query_norm, query_token_set)
        candidates = []

        for entry in self.entries:
            if not self._role_allowed(entry, role):
                continue
            semantic = self._cosine(entry.id, query_vector, query_norm)
            keyword = self._keyword_score(entry.id, query_token_set)
            lexical = self._lexical_overlap(entry.id, query_token_set)
            intent_score = intent_scores.get(entry.main_intent, 0.0)
            confidence = max(
                semantic * 0.58 + keyword * 0.20 + lexical * 0.08 + intent_score * 0.14,
                keyword * 0.9,
                lexical * 0.72,
                intent_score * 0.64 if semantic > 0.12 or keyword > 0 else 0.0,
            )
            method = "semantica_tfidf"
            if intent_score >= semantic and intent_score >= keyword and intent_score >= lexical:
                method = "clasificacion_intencion"
            elif keyword >= semantic and keyword >= lexical:
                method = "palabras_clave"
            elif lexical > semantic:
                method = "coincidencia_lexica"

            candidates.append(
                {
                    "entry": entry,
                    "confidence": confidence,
                    "method": method,
                    "score_parts": {
                        "semantica": round(semantic, 4),
                        "keywords": round(keyword, 4),
                        "lexica": round(lexical, 4),
                        "intencion": round(intent_score, 4),
                    },
                }
            )

        return sorted(candidates, key=lambda item: item["confidence"], reverse=True)

    def _business_rule_entry(self, normalized: str, role: str) -> FAQEntry | None:
        """Aplica reglas deterministicas para consultas operativas de alta precision."""

        tokens = set(tokenize(normalized))
        rules = [
            ({"entrar", "cuenta"}, "uso_001"),
            ({"usuario", "entrar"}, "uso_001"),
            ({"caso", "saber"}, "uso_004"),
            ({"dejar", "constancia"}, "uso_003"),
            ({"aviso", "administrativo"}, "not_003"),
            ({"comunicado", "administracion"}, "not_003"),
            ({"campana", "numero"}, "not_007"),
            ({"entrada", "alguien"}, "seg_004"),
            ({"carro", "salida"}, "parq_001"),
            ({"autorizar", "persona"}, "vis_001"),
            ({"luz", "corredor"}, "mant_001"),
            ({"puerta"}, "mant_003"),
            ({"pelea", "vecino"}, "conv_003"),
            ({"perro", "suelto"}, "mas_001"),
            ({"multa"}, "adm_002"),
            ({"cuanto", "pagar"}, "adm_002"),
            ({"celular", "administrador"}, "adm_012"),
            ({"hora", "oficina"}, "adm_001"),
        ]
        for required_tokens, entry_id in rules:
            entry = self._entry_by_id.get(entry_id)
            if entry and required_tokens <= tokens and self._role_allowed(entry, role):
                return entry
        return None

    def _cosine(self, entry_id: str, query_vector: dict[str, float], query_norm: float) -> float:
        vector = self._vectors.get(entry_id, {})
        dot = sum(query_vector[token] * vector.get(token, 0.0) for token in query_vector)
        return max(0.0, min(1.0, dot / (query_norm * self._norms.get(entry_id, 1.0))))

    def _classify_intents(
        self,
        query_vector: dict[str, float],
        query_norm: float,
        query_tokens: set[str],
    ) -> dict[str, float]:
        """Clasifica intenciones principales como senal adicional de recuperacion."""

        scores = {}
        for intent_id, vector in self._intent_vectors.items():
            dot = sum(query_vector[token] * vector.get(token, 0.0) for token in query_vector)
            semantic = max(0.0, min(1.0, dot / (query_norm * self._intent_norms.get(intent_id, 1.0))))
            keywords = self._intent_keywords.get(intent_id, set())
            keyword_score = 0.0
            if keywords:
                keyword_score = min(1.0, len(query_tokens & keywords) / max(2, min(len(keywords), 8)))
            scores[intent_id] = max(semantic * 0.72 + keyword_score * 0.28, keyword_score * 0.82)
        return scores

    def _keyword_score(self, entry_id: str, query_tokens: set[str]) -> float:
        keywords = self._entry_keywords.get(entry_id, set())
        if not keywords:
            return 0.0
        overlap = len(query_tokens & keywords)
        return min(1.0, overlap / max(2, min(len(keywords), 5)))

    def _lexical_overlap(self, entry_id: str, query_tokens: set[str]) -> float:
        entry_tokens = set(self._entry_tokens.get(entry_id, Counter()))
        if not entry_tokens or not query_tokens:
            return 0.0
        return len(query_tokens & entry_tokens) / len(query_tokens | entry_tokens)

    def _role_allowed(self, entry: FAQEntry, role: str) -> bool:
        return role in entry.allowed_roles and entry.is_active()

    def _is_ambiguous(self, best: dict[str, Any], second: dict[str, Any] | None) -> bool:
        if not second:
            return False
        if best["entry"].main_intent == second["entry"].main_intent:
            return False
        return (best["confidence"] - second["confidence"]) < AMBIGUITY_MARGIN

    def _clarification_options(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        options = []
        seen_main_intents = set()
        for item in candidates:
            entry = item["entry"]
            if entry.main_intent in seen_main_intents:
                continue
            seen_main_intents.add(entry.main_intent)
            options.append(
                {
                    "id": entry.id,
                    "pregunta": entry.question,
                    "categoria": entry.category,
                    "intencion_principal": entry.main_intent,
                    "subintencion": entry.intent,
                    "confianza": round(item["confidence"], 4),
                    "estado_verificacion": entry.verification_status,
                    "vigencia": entry.validity_status,
                }
            )
            if len(options) >= MAX_OPTIONS:
                break
        return options

    def _answer_payload(
        self,
        entry: FAQEntry,
        *,
        confidence: float,
        method: str,
        mode: str,
        started: float,
        score_parts: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        mode = "segura" if not entry.verified else mode
        return {
            "action": "answer",
            "respuesta": entry.answer,
            "mode": mode,
            "provider": "local",
            "model": "commusafe-local-hybrid-v3",
            "confidence": round(confidence, 4),
            "intent": entry.main_intent,
            "subintent": entry.intent,
            "entry_id": entry.id,
            "category": entry.category,
            "method": method,
            "verified": entry.verified,
            "verification_status": entry.verification_status,
            "validity_status": entry.validity_status,
            "valid_from": entry.valid_from,
            "valid_until": entry.valid_until,
            "requires_validation": not entry.verified,
            "options": [],
            "score_parts": score_parts or {},
            "updated_at": entry.updated_at,
            "latency_ms": self._elapsed_ms(started),
        }

    def _exact_ambiguity_payload(self, entries: list[FAQEntry], started: float) -> dict[str, Any]:
        options = [
            {
                "id": entry.id,
                "pregunta": entry.question,
                "categoria": entry.category,
                "intencion_principal": entry.main_intent,
                "subintencion": entry.intent,
                "confianza": 1.0,
                "estado_verificacion": entry.verification_status,
                "vigencia": entry.validity_status,
            }
            for entry in entries[:MAX_OPTIONS]
        ]
        first = entries[0]
        return {
            "action": "clarify",
            "respuesta": self._build_clarification(options),
            "mode": "aclaracion",
            "provider": "local",
            "model": "commusafe-local-hybrid-v3",
            "confidence": 1.0,
            "intent": first.main_intent,
            "subintent": first.intent,
            "entry_id": first.id,
            "category": first.category,
            "method": "aclaracion_por_coincidencia_exacta_ambigua",
            "verified": all(entry.verified for entry in entries),
            "verification_status": first.verification_status,
            "validity_status": first.validity_status,
            "valid_from": first.valid_from,
            "valid_until": first.valid_until,
            "requires_validation": any(not entry.verified for entry in entries),
            "options": options,
            "latency_ms": self._elapsed_ms(started),
        }

    def _safe_response(self, started: float, *, reason: str) -> dict[str, Any]:
        return {
            "action": "safe",
            "respuesta": (
                "Solo puedo apoyar consultas relacionadas con Remansos del Norte y CommuSafe. "
                "No encuentro informacion verificada suficiente para responder esa consulta. "
                "Te recomiendo validarlo con administracion."
            ),
            "mode": "segura",
            "provider": "local",
            "model": "commusafe-local-hybrid-v3",
            "confidence": 0.0,
            "intent": "sin_intencion_confiable",
            "subintent": "",
            "entry_id": "",
            "category": "seguridad_respuesta",
            "method": reason,
            "verified": True,
            "verification_status": "VERIFICADA",
            "validity_status": "VIGENTE",
            "valid_from": "",
            "valid_until": "",
            "requires_validation": True,
            "options": [],
            "latency_ms": self._elapsed_ms(started),
        }

    def _build_clarification(self, options: list[dict[str, Any]]) -> str:
        lines = [
            "Puedo ayudarte, pero necesito precisar mejor la consulta. Elige una opcion o escribeme mas detalles:"
        ]
        for index, option in enumerate(options, start=1):
            lines.append(f"{index}. {option['pregunta']}")
        lines.append("Responde con el numero de la opcion o cuentame un poco mas para orientarte mejor.")
        return "\n".join(lines)

    def _elapsed_ms(self, started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    def export_entries(self) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in self.entries]

    def explain_candidates(self, message: str, role: str = "RESIDENTE", limit: int = 5) -> dict[str, Any]:
        """Devuelve candidatos ordenados sin exponer estructuras internas mutables."""

        started = time.perf_counter()
        normalized = normalize_text(message)
        role = (role or "RESIDENTE").upper()
        safe_limit = min(max(int(limit or 5), 1), 10)
        candidates = self._score_candidates(normalized, role) if normalized else []
        return {
            "mensaje_normalizado": normalized,
            "rol": role,
            "total_candidatos": len(candidates),
            "candidatos": [
                {
                    "id": item["entry"].id,
                    "pregunta": item["entry"].question,
                    "categoria": item["entry"].category,
                    "intencion_principal": item["entry"].main_intent,
                    "subintencion": item["entry"].intent,
                    "confianza": round(item["confidence"], 4),
                    "metodo": item["method"],
                    "score_parts": item["score_parts"],
                    "estado_verificacion": item["entry"].verification_status,
                    "vigencia": item["entry"].validity_status,
                    "requiere_validacion": not item["entry"].verified,
                }
                for item in candidates[:safe_limit]
            ],
            "latencia_ms": self._elapsed_ms(started),
        }

    def stats(self) -> dict[str, Any]:
        by_category: dict[str, int] = defaultdict(int)
        for entry in self.entries:
            by_category[entry.category] += 1
        return {
            "total_faq": len(self.entries),
            "verificadas": sum(1 for entry in self.entries if entry.verified),
            "pendientes_validacion": sum(1 for entry in self.entries if not entry.verified),
            "vigentes": sum(1 for entry in self.entries if entry.is_active()),
            "vencidas": sum(1 for entry in self.entries if not entry.is_active()),
            "categorias": len(by_category),
            "categorias_detalle": dict(sorted(by_category.items())),
            "colisiones_exactas_controladas": sum(1 for entries in self._exact_index.values() if len(entries) > 1),
            "clasificador_intenciones": "centroides_tfidf_por_intencion",
            "umbral_alto": HIGH_CONFIDENCE_THRESHOLD,
            "umbral_medio": MEDIUM_CONFIDENCE_THRESHOLD,
            "modelo": "commusafe-local-hybrid-v3",
        }


ENGINE = LocalAssistantEngine()
ENGINE_REVISION = "static"
ENGINE_LAST_CHECK = 0.0
ENGINE_REFRESH_SECONDS = 5.0
ENGINE_LOCK = RLock()


@lru_cache(maxsize=512)
def resolve_local_answer_cached(message: str, role: str = "RESIDENTE") -> dict[str, Any]:
    """Resolucion cacheada por texto normalizado y rol."""

    normalized = normalize_text(message)
    return ENGINE.resolve(normalized, (role or "RESIDENTE").upper())


def refresh_local_engine(force: bool = False) -> bool:
    """Recarga atomica del indice cuando cambia conocimiento aprobado."""

    global ENGINE, ENGINE_LAST_CHECK, ENGINE_REVISION

    now = time.monotonic()
    with ENGINE_LOCK:
        if not force and now - ENGINE_LAST_CHECK < ENGINE_REFRESH_SECONDS:
            return False

        entries, revision = obtener_snapshot_conocimiento()
        ENGINE_LAST_CHECK = now
        if revision == ENGINE_REVISION:
            return False

        ENGINE = LocalAssistantEngine(entries)
        ENGINE_REVISION = revision
        resolve_local_answer_cached.cache_clear()
        return True


def resolve_local_answer(message: str, role: str = "RESIDENTE") -> dict[str, Any]:
    # lru_cache comparte el mismo objeto entre llamadas. Django puede enriquecer
    # el resultado con errores de fallback o metadatos, por eso cada request recibe
    # una copia defensiva y nunca el diccionario cacheado mutable.
    refresh_local_engine()
    return deepcopy(resolve_local_answer_cached(message, role))


def local_engine_stats() -> dict[str, Any]:
    refresh_local_engine()
    cache_info = resolve_local_answer_cached.cache_info()
    return {
        **ENGINE.stats(),
        "revision_conocimiento": ENGINE_REVISION,
        "cache": {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "maxsize": cache_info.maxsize,
            "currsize": cache_info.currsize,
        },
    }


def explain_local_candidates(message: str, role: str = "RESIDENTE", limit: int = 5) -> dict[str, Any]:
    refresh_local_engine()
    return ENGINE.explain_candidates(message, role, limit)


def export_local_entries() -> list[dict[str, Any]]:
    refresh_local_engine()
    return ENGINE.export_entries()


def clear_local_engine_cache() -> dict[str, Any]:
    resolve_local_answer_cached.cache_clear()
    refresh_local_engine(force=True)
    return local_engine_stats()
