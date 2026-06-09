"""Servicio Flask auxiliar para comprension local de CommuBot.

Uso local:
    python -m asistente.nlp_flask_service

Uso WSGI recomendado cuando se despliega como proceso separado:
    gunicorn asistente.nlp_flask_service:app --bind 127.0.0.1:5055 --workers 2 --threads 4

El backend Django no depende obligatoriamente de este proceso. Si el servicio no
esta disponible, Django sigue resolviendo con el mismo motor local en memoria.
"""

from __future__ import annotations

import hmac
import logging
import os
import time
import uuid
from functools import wraps
from threading import RLock
from typing import Any

from flask import Flask, g, jsonify, request

from .evaluation import evaluate_all
from .local_engine import (
    clear_local_engine_cache,
    explain_local_candidates,
    export_local_entries,
    local_engine_stats,
    resolve_local_answer,
)
from .model_selection import train_compare_select_models
from .training_dataset import build_professional_dataset, dataset_summary, validate_professional_dataset


LOGGER = logging.getLogger("commusafe.nlp_service")
LOCAL_REMOTE_ADDRS = {"127.0.0.1", "::1", "localhost"}
MAX_MESSAGE_LENGTH = int(os.environ.get("COMMUSAFE_NLP_MAX_MESSAGE_LENGTH", "1200"))
MAX_BATCH_SIZE = int(os.environ.get("COMMUSAFE_NLP_MAX_BATCH_SIZE", "25"))
MODEL_OPERATION_LOCK = RLock()
STARTED_AT = time.time()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    @app.before_request
    def start_request_timer():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.started_at = time.perf_counter()

    @app.after_request
    def add_operational_headers(response):
        elapsed_ms = int((time.perf_counter() - g.get("started_at", time.perf_counter())) * 1000)
        response.headers["X-CommuSafe-Request-ID"] = g.get("request_id", "")
        response.headers["X-CommuSafe-NLP-Latency-ms"] = str(elapsed_ms)
        LOGGER.info(
            "nlp_request",
            extra={
                "request_id": g.get("request_id"),
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "latency_ms": elapsed_ms,
                "remote_addr": request.remote_addr,
            },
        )
        return response

    def require_service_key(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            expected_key = os.environ.get("COMMUSAFE_NLP_SERVICE_KEY", "").strip()
            if expected_key:
                received = request.headers.get("X-CommuSafe-NLP-Key", "")
                if not hmac.compare_digest(received, expected_key):
                    return _error("Credencial del servicio NLP invalida.", 401, "credencial_invalida")
            elif request.remote_addr not in LOCAL_REMOTE_ADDRS:
                return _error(
                    "Configura COMMUSAFE_NLP_SERVICE_KEY para acceso remoto.",
                    403,
                    "clave_requerida",
                )
            return view_func(*args, **kwargs)

        return wrapped

    @app.errorhandler(404)
    def not_found(_error_obj):
        return _error("Ruta del servicio NLP no encontrada.", 404, "ruta_no_encontrada")

    @app.errorhandler(405)
    def method_not_allowed(_error_obj):
        return _error("Metodo HTTP no permitido para esta ruta.", 405, "metodo_no_permitido")

    @app.errorhandler(ValueError)
    def validation_error(error):
        return _error(str(error), 400, "solicitud_invalida")

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        LOGGER.exception("nlp_unhandled_exception", extra={"request_id": g.get("request_id")})
        return _error("El servicio NLP no pudo completar la solicitud.", 500, "error_interno", str(error))

    @app.get("/health")
    @app.get("/v1/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "servicio": "commusafe-nlp",
                "version_api": "v1",
                "uptime_segundos": int(time.time() - STARTED_AT),
                "seguridad": _security_status(),
                "motor": local_engine_stats(),
                "cache": _cache_stats(),
            }
        )

    @app.post("/infer")
    @app.post("/v1/infer")
    @require_service_key
    def infer():
        payload = _json_payload()
        mensaje = _required_text(payload, "mensaje")
        rol = _normalize_role(payload.get("rol", "RESIDENTE"))
        incluir_candidatos = bool(payload.get("incluir_candidatos", False))

        result = resolve_local_answer(mensaje, rol)
        response = {
            "resultado": result,
            "servicio": _service_metadata("inferencia_local"),
        }
        if incluir_candidatos:
            response["seleccion_respuesta"] = explain_local_candidates(
                mensaje,
                rol,
                int(payload.get("limite_candidatos", 5) or 5),
            )
        return jsonify(response)

    @app.post("/v1/infer/batch")
    @require_service_key
    def infer_batch():
        payload = _json_payload()
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            return _error("Debes enviar una lista no vacia en items.", 400, "items_invalidos")
        if len(items) > MAX_BATCH_SIZE:
            return _error(
                f"El lote supera el maximo permitido de {MAX_BATCH_SIZE} mensajes.",
                400,
                "lote_demasiado_grande",
            )

        results = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                return _error(f"El item {index} debe ser un objeto JSON.", 400, "item_invalido")
            mensaje = _required_text(item, "mensaje")
            rol = _normalize_role(item.get("rol", payload.get("rol", "RESIDENTE")))
            results.append(
                {
                    "indice": index,
                    "mensaje": mensaje,
                    "rol": rol,
                    "resultado": resolve_local_answer(mensaje, rol),
                }
            )
        return jsonify({"resultados": results, "servicio": _service_metadata("inferencia_lote")})

    @app.get("/knowledge")
    @app.get("/v1/knowledge")
    @require_service_key
    def knowledge():
        incluir_entradas = request.args.get("entries", "1") != "0"
        payload: dict[str, Any] = {
            "stats": local_engine_stats(),
            "servicio": _service_metadata("conocimiento"),
        }
        if incluir_entradas:
            payload["entries"] = export_local_entries()
        return jsonify(payload)

    @app.post("/v1/candidates")
    @require_service_key
    def candidates():
        payload = _json_payload()
        mensaje = _required_text(payload, "mensaje")
        rol = _normalize_role(payload.get("rol", "RESIDENTE"))
        limit = int(payload.get("limite", 5) or 5)
        return jsonify(
            {
                "seleccion_respuesta": explain_local_candidates(mensaje, rol, limit),
                "servicio": _service_metadata("seleccion_respuesta"),
            }
        )

    @app.post("/v1/evaluate")
    @require_service_key
    def evaluate():
        with MODEL_OPERATION_LOCK:
            started = time.perf_counter()
            payload = evaluate_all()
            payload["servicio"] = _service_metadata(
                "evaluacion",
                latencia_ms=int((time.perf_counter() - started) * 1000),
            )
            return jsonify(payload)

    @app.post("/v1/models/select")
    @require_service_key
    def model_selection():
        with MODEL_OPERATION_LOCK:
            started = time.perf_counter()
            payload = train_compare_select_models()
            payload["servicio"] = _service_metadata(
                "seleccion_modelo",
                latencia_ms=int((time.perf_counter() - started) * 1000),
            )
            return jsonify(payload)

    @app.post("/v1/retrain")
    @require_service_key
    def retrain():
        with MODEL_OPERATION_LOCK:
            started = time.perf_counter()
            splits = build_professional_dataset()
            errors = validate_professional_dataset(splits)
            stats = clear_local_engine_cache()
            return jsonify(
                {
                    "estado": "ok" if not errors else "con_observaciones",
                    "errores_dataset": errors,
                    "dataset": dataset_summary(splits),
                    "motor": stats,
                    "accion": "cache_recargada_y_dataset_validado",
                    "nota": (
                        "El motor local recargo el catalogo inicial y las entradas administradas "
                        "aprobadas y vigentes disponibles para este proceso."
                    ),
                    "servicio": _service_metadata(
                        "reentrenamiento_logico",
                        latencia_ms=int((time.perf_counter() - started) * 1000),
                    ),
                }
            )

    return app


def _json_payload() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValueError("El cuerpo debe ser JSON valido.")
    if not isinstance(payload, dict):
        raise ValueError("El cuerpo JSON debe ser un objeto.")
    return payload


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = str(payload.get(field, "")).strip()
    if not value:
        raise ValueError(f"El campo {field} es obligatorio.")
    if len(value) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"El campo {field} supera {MAX_MESSAGE_LENGTH} caracteres.")
    return value


def _normalize_role(value: Any) -> str:
    role = str(value or "RESIDENTE").strip().upper()
    if role not in {"RESIDENTE", "VIGILANTE", "ADMINISTRADOR"}:
        raise ValueError("El rol debe ser RESIDENTE, VIGILANTE o ADMINISTRADOR.")
    return role


def _security_status() -> dict[str, Any]:
    has_key = bool(os.environ.get("COMMUSAFE_NLP_SERVICE_KEY", "").strip())
    host = os.environ.get("COMMUSAFE_NLP_HOST", "127.0.0.1")
    return {
        "clave_configurada": has_key,
        "host_configurado": host,
        "acceso_remoto_permitido": has_key,
        "politica": "clave_requerida_para_remoto" if has_key else "solo_localhost",
    }


def _cache_stats() -> dict[str, Any]:
    return local_engine_stats()["cache"]


def _service_metadata(operation: str, latencia_ms: int | None = None) -> dict[str, Any]:
    payload = {
        "operacion": operation,
        "servicio": "commusafe-nlp",
        "version_api": "v1",
        "request_id": g.get("request_id", ""),
        "thread_safe": True,
        "modelo_activo": local_engine_stats().get("modelo", "commusafe-local-hybrid-v3"),
    }
    if latencia_ms is not None:
        payload["latencia_ms"] = latencia_ms
    return payload


def _error(detail: str, status_code: int, code: str, technical_detail: str = ""):
    payload = {
        "detail": detail,
        "codigo": code,
        "request_id": g.get("request_id", ""),
        "servicio": "commusafe-nlp",
    }
    if os.environ.get("COMMUSAFE_NLP_DEBUG_ERRORS", "") == "1" and technical_detail:
        payload["detalle_tecnico"] = technical_detail
    return jsonify(payload), status_code


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("COMMUSAFE_NLP_LOG_LEVEL", "INFO"))
    port = int(os.environ.get("COMMUSAFE_NLP_PORT", "5055"))
    host = os.environ.get("COMMUSAFE_NLP_HOST", "127.0.0.1")
    app.run(host=host, port=port, threaded=True)
