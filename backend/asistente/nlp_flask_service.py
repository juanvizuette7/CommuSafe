"""Servicio Flask auxiliar para comprension local de CommuBot.

Uso local:
    python -m asistente.nlp_flask_service

Endpoints:
    GET  /health
    POST /infer      {"mensaje": "...", "rol": "RESIDENTE"}
    GET  /knowledge

El backend Django no depende obligatoriamente de este proceso: usa el mismo
motor en memoria y puede seguir funcionando aunque Flask no este levantado.
"""

from __future__ import annotations

import os
from functools import wraps

from flask import Flask, jsonify, request

from .local_engine import ENGINE, resolve_local_answer


def create_app() -> Flask:
    app = Flask(__name__)

    def require_service_key(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            expected_key = os.environ.get("COMMUSAFE_NLP_SERVICE_KEY", "").strip()
            if expected_key:
                received = request.headers.get("X-CommuSafe-NLP-Key", "")
                if received != expected_key:
                    return jsonify({"detail": "Credencial del servicio NLP invalida."}), 401
            return view_func(*args, **kwargs)

        return wrapped

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "servicio": "commusafe-nlp", **ENGINE.stats()})

    @app.post("/infer")
    @require_service_key
    def infer():
        payload = request.get_json(silent=True) or {}
        mensaje = str(payload.get("mensaje", "")).strip()
        rol = str(payload.get("rol", "RESIDENTE")).strip().upper()
        if not mensaje:
            return jsonify({"detail": "El mensaje es obligatorio."}), 400
        return jsonify(resolve_local_answer(mensaje, rol))

    @app.get("/knowledge")
    @require_service_key
    def knowledge():
        return jsonify({"stats": ENGINE.stats(), "entries": ENGINE.export_entries()})

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("COMMUSAFE_NLP_PORT", "5055"))
    app.run(host="0.0.0.0", port=port, threaded=True)
