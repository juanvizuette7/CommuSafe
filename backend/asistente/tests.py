"""Pruebas del modulo de asistente virtual."""

import json
import tempfile
import unicodedata
from collections import Counter
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .knowledge_base import KNOWLEDGE_BASE_SECTIONS, render_knowledge_base
from .evaluation import build_challenge_dataset, build_dataset, calibrate_thresholds
from .local_engine import (
    AMBIGUITY_MARGIN,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    normalize_text,
    resolve_local_answer,
)
from .local_knowledge import FAQ_ENTRIES
from .model_selection import train_compare_select_models
from .models import AsistenteRespuestaLog, ConversacionAsistente, MensajeAsistente
from .nlp_flask_service import app as flask_app
from .services import (
    MAX_LLM_HISTORY_CHARS,
    MAX_LLM_HISTORY_MESSAGES,
    SYSTEM_PROMPT,
    _compactar_historial_para_ia,
    construir_system_prompt,
)
from .throttles import AsistenteChatThrottle, AsistenteLecturaThrottle
from .training_dataset import (
    EXAMPLES_PER_INTENT,
    REQUIRED_STYLES,
    SPLIT_RATIOS,
    build_professional_dataset,
    dataset_summary,
    validate_professional_dataset,
)
from .taxonomy import MAIN_INTENTS, validate_taxonomy
from .views import _api_llm_configurada, _extraer_texto_anthropic, _normalizar_historial, _respuesta_fallback
from .views import ChatAsistenteView, ChatHealthView, ConversacionAsistenteViewSet


Usuario = get_user_model()


def normalizar_texto(texto):
    """Normaliza acentos para que las pruebas no dependan de codificación de consola."""

    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()


@override_settings(LLM_API_KEY="", GEMINI_API_KEY="", LLM_PROVIDER="gemini")
class ChatAsistenteFallbackTests(APITestCase):
    """Pruebas del asistente hibrido local-first."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="asistente@test.com",
            password="Segura2026*",
            nombre="Laura",
            apellido="Rios",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )

    def test_responde_con_fallback_para_horarios(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            reverse("asistente:chat"),
            {
                "mensaje": "Cual es el horario de las areas comunes?",
                "historial": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data["modo"], {"local", "semantica", "aclaracion", "segura"})
        self.assertIn("6:00", normalizar_texto(response.data["respuesta"]))

    def test_limita_historial_a_ultimos_ocho_mensajes(self):
        self.client.force_authenticate(self.usuario)
        historial = [{"rol": "usuario", "contenido": f"Mensaje {indice}"} for indice in range(12)]
        response = self.client.post(
            reverse("asistente:chat"),
            {
                "mensaje": "Necesito ayuda con una norma.",
                "historial": historial,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data["modo"], {"local", "semantica", "aclaracion", "segura"})

    def test_consulta_fuera_de_alcance_da_respuesta_controlada(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            reverse("asistente:chat"),
            {
                "mensaje": "Dime el precio del dolar hoy.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("remansos del norte", normalizar_texto(response.data["respuesta"]))

    def test_registra_log_tecnico_de_respuesta_local(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            reverse("asistente:chat"),
            {"mensaje": "Como reporto un incidente?"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = AsistenteRespuestaLog.objects.latest("fecha_creacion")
        self.assertEqual(log.usuario, self.usuario)
        self.assertIn(log.modo, {"local", "semantica"})
        self.assertEqual(log.proveedor, "local")
        self.assertEqual(log.intencion, "reportar_incidente")
        self.assertEqual(log.metadata["subintent"], "crear_incidente")
        self.assertIsNotNone(log.confianza)

    @override_settings(LLM_API_KEY="clave-real", GEMINI_API_KEY="", LLM_PROVIDER="anthropic")
    @patch("asistente.services.Anthropic")
    def test_preguntas_conocidas_no_usan_ia_externa(self, anthropic_mock):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            reverse("asistente:chat"),
            {"mensaje": "Como reporto un incidente?"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data["modo"], {"local", "semantica"})
        anthropic_mock.assert_not_called()

    def test_health_expone_motor_local(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.get(reverse("asistente:health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["arquitectura"], "hibrida_local_primero")
        self.assertGreaterEqual(response.data["motor_local"]["total_faq"], 100)

    def test_endpoints_declaran_throttling_del_asistente(self):
        self.assertEqual(ChatAsistenteView.throttle_classes, [AsistenteChatThrottle])
        self.assertEqual(ChatHealthView.throttle_classes, [AsistenteLecturaThrottle])

        viewset = ConversacionAsistenteViewSet()
        viewset.action = "enviar"
        self.assertIsInstance(viewset.get_throttles()[0], AsistenteChatThrottle)
        viewset.action = "list"
        self.assertIsInstance(viewset.get_throttles()[0], AsistenteLecturaThrottle)

    def test_acepta_historial_con_campo_mensaje_y_roles_alias(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            reverse("asistente:chat"),
            {
                "mensaje": "Que hago ante una emergencia?",
                "historial": [
                    {"rol": "usuario", "mensaje": "Hola"},
                    {"rol": "asistente", "mensaje": "Buenos dias"},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data["modo"], {"local", "semantica", "aclaracion", "segura"})

    def test_rechaza_mensaje_de_historial_sin_contenido(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            reverse("asistente:chat"),
            {
                "mensaje": "Necesito orientacion",
                "historial": [{"rol": "user"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("historial", response.data)

    def test_fallback_para_cuotas_normas_y_app(self):
        self.client.force_authenticate(self.usuario)

        cuotas = self.client.post(
            reverse("asistente:chat"),
            {"mensaje": "Como va mi cuota de administracion?"},
            format="json",
        )
        normas = self.client.post(
            reverse("asistente:chat"),
            {"mensaje": "Que norma aplica para mascotas?"},
            format="json",
        )
        app = self.client.post(
            reverse("asistente:chat"),
            {"mensaje": "Que puedo hacer en la app de CommuSafe?"},
            format="json",
        )

        self.assertIn("administracion", normalizar_texto(cuotas.data["respuesta"]))
        self.assertIn("convivencia", normalizar_texto(normas.data["respuesta"]))
        self.assertIn("commusafe", normalizar_texto(app.data["respuesta"]))

    def test_endpoint_requiere_autenticacion(self):
        response = self.client.post(
            reverse("asistente:chat"),
            {"mensaje": "Hola"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatAsistenteHelpersTests(APITestCase):
    """Pruebas unitarias de helpers de la vista del asistente."""

    def test_api_llm_configurada(self):
        with override_settings(LLM_API_KEY="", GEMINI_API_KEY=""):
            self.assertFalse(_api_llm_configurada())
        with override_settings(LLM_API_KEY="REEMPLAZAR_KEY", GEMINI_API_KEY=""):
            self.assertFalse(_api_llm_configurada())
        with override_settings(LLM_API_KEY="clave-real", GEMINI_API_KEY=""):
            self.assertTrue(_api_llm_configurada())
        with override_settings(LLM_API_KEY="", GEMINI_API_KEY="clave-real"):
            with patch("asistente.services.genai", object()):
                self.assertTrue(_api_llm_configurada())

        with override_settings(LLM_API_KEY="", GEMINI_API_KEY="clave-real"):
            with patch("asistente.services.genai", None):
                self.assertFalse(_api_llm_configurada())

    def test_normalizar_historial(self):
        historial = [
            {"rol": "usuario", "contenido": " Hola "},
            {"rol": "asistente", "contenido": " Mundo "},
        ]

        normalizado = _normalizar_historial(historial)

        self.assertEqual(normalizado[0], {"role": "user", "content": "Hola"})
        self.assertEqual(normalizado[1], {"role": "assistant", "content": "Mundo"})

    def test_compacta_historial_para_reducir_tokens_ia(self):
        historial = [
            {"rol": "usuario", "contenido": f"Mensaje {indice} " + ("x" * 800)}
            for indice in range(30)
        ]

        compacto = _compactar_historial_para_ia(historial)

        self.assertLessEqual(len(compacto), MAX_LLM_HISTORY_MESSAGES)
        self.assertLessEqual(sum(len(item["content"]) for item in compacto), MAX_LLM_HISTORY_CHARS)
        self.assertIn("Mensaje 29", compacto[-1]["content"])

    def test_extraer_texto_anthropic(self):
        respuesta = SimpleNamespace(
            content=[
                SimpleNamespace(text="Linea 1"),
                SimpleNamespace(text="  "),
                SimpleNamespace(text="Linea 2"),
            ]
        )

        texto = _extraer_texto_anthropic(respuesta)

        self.assertEqual(texto, "Linea 1\nLinea 2")

    def test_respuesta_fallback_default(self):
        texto = _respuesta_fallback("consulta completamente desconocida")
        self.assertIn("solo puedo apoyar", normalizar_texto(texto))

    def test_base_conocimiento_incluye_contexto_operativo(self):
        contenido = normalizar_texto(render_knowledge_base())

        self.assertGreaterEqual(len(KNOWLEDGE_BASE_SECTIONS), 10)
        self.assertIn("pasto", contenido)
        self.assertIn("narino", contenido)
        self.assertIn("visitantes", contenido)
        self.assertIn("parqueaderos", contenido)
        self.assertIn("mascotas", contenido)
        self.assertIn("conversaciones del asistente quedan guardadas", contenido)

    def test_prompt_no_usa_marcadores_de_datos_no_reales(self):
        contenido = normalizar_texto(SYSTEM_PROMPT)

        self.assertIn("segun la informacion registrada en commusafe", contenido)
        self.assertNotIn("informacion falsa", contenido)
        self.assertNotIn("datos inventados", contenido)
        self.assertNotIn("datos simulados", contenido)

    def test_contexto_enviado_a_ia_minimiza_datos_personales(self):
        usuario = Usuario.objects.create_user(
            email="privacidad-contexto@test.com",
            password="Segura2026*",
            nombre="NombrePrivado",
            apellido="ApellidoPrivado",
            unidad_residencial="Apto Privado 999",
            rol=Usuario.Rol.RESIDENTE,
        )

        prompt = normalizar_texto(construir_system_prompt(usuario))

        self.assertIn("rol del usuario autenticado", prompt)
        self.assertNotIn("nombreprivado", prompt)
        self.assertNotIn("apellidoprivado", prompt)
        self.assertNotIn("apto privado 999", prompt)

    def test_base_local_es_diversa_verificable_y_vigente(self):
        self.assertGreaterEqual(len(FAQ_ENTRIES), 100)
        self.assertEqual(len({entry.id for entry in FAQ_ENTRIES}), len(FAQ_ENTRIES))
        self.assertEqual(len({entry.intent for entry in FAQ_ENTRIES}), len(FAQ_ENTRIES))
        self.assertEqual(len({entry.main_intent for entry in FAQ_ENTRIES}), len(MAIN_INTENTS))
        self.assertEqual(validate_taxonomy({entry.id for entry in FAQ_ENTRIES}), [])
        self.assertEqual(len({entry.question.lower() for entry in FAQ_ENTRIES}), len(FAQ_ENTRIES))
        self.assertGreaterEqual(len({entry.category for entry in FAQ_ENTRIES}), 10)

        for entry in FAQ_ENTRIES:
            self.assertTrue(entry.verification_status)
            self.assertEqual(entry.validity_status, "VIGENTE")
            self.assertTrue(entry.valid_from)
            self.assertGreaterEqual(len(entry.keywords), 3)
            self.assertGreaterEqual(len(entry.variations), 2)

    def test_respuestas_pendientes_son_seguras(self):
        pendientes = [entry for entry in FAQ_ENTRIES if not entry.verified]
        self.assertGreaterEqual(len(pendientes), 1)

        for entry in pendientes:
            respuesta = normalizar_texto(entry.answer)
            self.assertTrue(
                any(
                    termino in respuesta
                    for termino in ["administracion", "validar", "validarse", "verificar", "no encuentro", "no emite"]
                ),
                entry.id,
            )

    def test_comando_valida_base_conocimiento(self):
        salida = StringIO()
        call_command("validar_base_conocimiento", stdout=salida)
        contenido = salida.getvalue()

        self.assertIn('"estado": "ok"', contenido)
        self.assertIn("al_menos_100_preguntas_diferentes", contenido)

    def test_servicio_flask_restringe_acceso_remoto_sin_clave(self):
        client = flask_app.test_client()

        remoto = client.post(
            "/infer",
            json={"mensaje": "Como reporto un incidente?", "rol": "RESIDENTE"},
            environ_base={"REMOTE_ADDR": "203.0.113.10"},
        )
        local = client.post(
            "/infer",
            json={"mensaje": "Como reporto un incidente?", "rol": "RESIDENTE"},
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        )

        self.assertEqual(remoto.status_code, 403)
        self.assertEqual(local.status_code, 200)
        self.assertEqual(local.json["action"], "answer")

    def test_motor_expone_intencion_principal_y_subintencion(self):
        resultado = resolve_local_answer("Como reporto un incidente?", "RESIDENTE")

        self.assertEqual(resultado["action"], "answer")
        self.assertEqual(resultado["intent"], "reportar_incidente")
        self.assertEqual(resultado["subintent"], "crear_incidente")
        self.assertEqual(resultado["provider"], "local")

    def test_umbrales_activos_coinciden_con_calibracion(self):
        splits = build_dataset()
        calibracion = calibrate_thresholds(splits["validation"], build_challenge_dataset())

        self.assertEqual(calibracion["umbral_alto"], HIGH_CONFIDENCE_THRESHOLD)
        self.assertEqual(calibracion["umbral_medio"], MEDIUM_CONFIDENCE_THRESHOLD)
        self.assertEqual(calibracion["margen_ambiguedad"], AMBIGUITY_MARGIN)
        self.assertEqual(calibracion["respuestas_directas_incorrectas"], 0)

    def test_motor_cubre_estilos_y_casos_de_seguridad(self):
        casos = [
            ("Como reporto un incidente?", "answer", "reportar_incidente"),
            ("komo reporto un insidente", "answer", "reportar_incidente"),
            ("parce no puedo entrar a la cuenta que hago", "answer", "acceso_sesion"),
            (
                "Tengo una situacion relacionada con un dano en una zona comun y necesito orientacion detallada.",
                "answer",
                "convivencia_entorno",
            ),
            ("quien gano el partido de futbol ayer", "safe", "sin_intencion_confiable"),
        ]

        for mensaje, accion, intencion in casos:
            with self.subTest(mensaje=mensaje):
                resultado = resolve_local_answer(mensaje, "RESIDENTE")
                self.assertEqual(resultado["action"], accion)
                self.assertEqual(resultado["intent"], intencion)

        no_verificada = resolve_local_answer("Cual es el horario de zonas comunes?", "RESIDENTE")
        self.assertEqual(no_verificada["action"], "answer")
        self.assertEqual(no_verificada["mode"], "segura")
        self.assertTrue(no_verificada["requires_validation"])

        ambigua = resolve_local_answer("Tengo una duda con un reporte y una alerta", "RESIDENTE")
        self.assertIn(ambigua["action"], {"clarify", "fallback_allowed"})
        self.assertNotEqual(ambigua["action"], "answer")

        ambigua_exacta = resolve_local_answer("musica alta", "RESIDENTE")
        self.assertEqual(ambigua_exacta["action"], "clarify")
        self.assertEqual(ambigua_exacta["method"], "aclaracion_por_coincidencia_exacta_ambigua")


class AsistenteTrainingDatasetTests(APITestCase):
    """Pruebas del dataset profesional usado para entrenar y evaluar intenciones."""

    def test_dataset_profesional_es_balanceado_y_coherente(self):
        splits = build_professional_dataset(seed=42)
        errores = validate_professional_dataset(splits)
        resumen = dataset_summary(splits)
        total_intenciones = len(MAIN_INTENTS)

        self.assertEqual(errores, [])
        self.assertEqual(resumen["total"], total_intenciones * EXAMPLES_PER_INTENT)
        self.assertEqual(resumen["intenciones"], total_intenciones)
        self.assertEqual(resumen["categorias"], 12)
        self.assertTrue(resumen["balanceado_por_intencion"])
        self.assertEqual(resumen["min_ejemplos_por_intencion"], EXAMPLES_PER_INTENT)
        self.assertEqual(resumen["max_ejemplos_por_intencion"], EXAMPLES_PER_INTENT)

        for split, ratio in SPLIT_RATIOS.items():
            self.assertEqual(
                resumen["splits"][split],
                total_intenciones * len(REQUIRED_STYLES) * ratio,
            )

        expected_holdout = total_intenciones * SPLIT_RATIOS["validation"]
        expected_train = total_intenciones * SPLIT_RATIOS["train"]
        for style in REQUIRED_STYLES:
            self.assertEqual(
                resumen["estilos"][style],
                total_intenciones * sum(SPLIT_RATIOS.values()),
            )
            self.assertEqual(resumen["estilos_por_split"]["train"][style], expected_train)
            self.assertEqual(resumen["estilos_por_split"]["validation"][style], expected_holdout)
            self.assertEqual(resumen["estilos_por_split"]["test"][style], expected_holdout)

        conteo_por_intencion = Counter()
        conteo_split_por_intencion: dict[str, Counter[str]] = {}
        for split, ejemplos in splits.items():
            for ejemplo in ejemplos:
                conteo_por_intencion[ejemplo.intent] += 1
                conteo_split_por_intencion.setdefault(ejemplo.intent, Counter())[split] += 1
                self.assertTrue(ejemplo.text)
                self.assertTrue(ejemplo.entry_id)
                self.assertTrue(ejemplo.subintent)
                self.assertIn(ejemplo.style, REQUIRED_STYLES)
                self.assertEqual(ejemplo.requires_admin_validation, not ejemplo.verified)

        self.assertEqual(set(conteo_por_intencion.values()), {EXAMPLES_PER_INTENT})
        for intent, conteo_split in conteo_split_por_intencion.items():
            self.assertEqual(conteo_split["train"], len(REQUIRED_STYLES) * SPLIT_RATIOS["train"], intent)
            self.assertEqual(
                conteo_split["validation"],
                len(REQUIRED_STYLES) * SPLIT_RATIOS["validation"],
                intent,
            )
            self.assertEqual(conteo_split["test"], len(REQUIRED_STYLES) * SPLIT_RATIOS["test"], intent)

    def test_dataset_no_repite_frases_entre_particiones(self):
        splits = build_professional_dataset(seed=42)
        textos_vistos: dict[str, str] = {}

        for split, ejemplos in splits.items():
            for ejemplo in ejemplos:
                normalizado = normalize_text(ejemplo.text)
                self.assertNotIn(
                    normalizado,
                    textos_vistos,
                    f"Texto repetido entre {textos_vistos.get(normalizado)} y {split}: {ejemplo.text}",
                )
                textos_vistos[normalizado] = split

    def test_comando_generar_dataset_exporta_json_validado(self):
        salida = StringIO()

        with tempfile.TemporaryDirectory() as tmp_dir:
            ruta_json = Path(tmp_dir) / "commusafe_dataset.json"
            call_command("generar_dataset_asistente", "--json", str(ruta_json), stdout=salida)

            payload = json.loads(salida.getvalue())
            exportado = json.loads(ruta_json.read_text(encoding="utf-8"))

        self.assertEqual(payload["estado"], "ok")
        self.assertEqual(payload["errores"], [])
        self.assertEqual(payload["resumen"]["json_exportado"], str(ruta_json))
        self.assertEqual(
            len(exportado["splits"]["train"]),
            len(MAIN_INTENTS) * len(REQUIRED_STYLES) * SPLIT_RATIOS["train"],
        )
        self.assertEqual(
            len(exportado["splits"]["validation"]),
            len(MAIN_INTENTS) * len(REQUIRED_STYLES) * SPLIT_RATIOS["validation"],
        )
        self.assertEqual(
            len(exportado["splits"]["test"]),
            len(MAIN_INTENTS) * len(REQUIRED_STYLES) * SPLIT_RATIOS["test"],
        )

    def test_comparacion_modelos_selecciona_por_generalizacion(self):
        payload = train_compare_select_models(seed=42)
        seleccionado = payload["modelo_seleccionado"]
        ranking_ids = [row["id"] for row in payload["ranking"]]

        self.assertEqual(seleccionado["id"], "hibrido_produccion_kb")
        self.assertIn("tfidf_centroides_palabra", ranking_ids)
        self.assertIn("tfidf_centroides_caracter", ranking_ids)
        self.assertIn("ensamble_word_char_35", ranking_ids)
        self.assertGreaterEqual(seleccionado["test_f1"], 0.90)
        self.assertEqual(seleccionado["directas_incorrectas_test"], 0)
        self.assertLess(
            seleccionado["sobreajuste_train_test"],
            0.10,
            "La seleccion no debe depender de memorizar el entrenamiento.",
        )


@override_settings(GEMINI_API_KEY="", LLM_PROVIDER="anthropic")
class ChatAsistenteIAModeTests(APITestCase):
    """Pruebas del flujo con IA configurada."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="ia@test.com",
            password="Segura2026*",
            nombre="Luis",
            apellido="Ramirez",
            unidad_residencial="Apto 404",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.url = reverse("asistente:chat")

    @override_settings(LLM_API_KEY="clave-real")
    @patch("asistente.services.Anthropic")
    def test_modo_ia_cuando_modelo_responde_texto(self, anthropic_mock):
        cliente = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(content=[SimpleNamespace(text="Respuesta IA")])
            )
        )
        anthropic_mock.return_value = cliente

        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            self.url,
            {
                "mensaje": "procedimiento biometrico de porteria para QR temporal",
                "historial": [{"rol": "usuario", "contenido": "hola"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["modo"], "ia")
        self.assertIn("Respuesta IA", response.data["respuesta"])

    @override_settings(LLM_API_KEY="clave-real")
    @patch("asistente.services.Anthropic")
    def test_modo_fallback_si_modelo_devuelve_vacio(self, anthropic_mock):
        cliente = SimpleNamespace(
            messages=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(content=[SimpleNamespace(text=" ")])
            )
        )
        anthropic_mock.return_value = cliente

        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            self.url,
            {"mensaje": "consulta operativa no registrada qwerty personalizada"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["modo"], "segura")

    @override_settings(LLM_API_KEY="clave-real")
    @patch("asistente.services.Anthropic", side_effect=Exception("fallo"))
    def test_modo_fallback_si_hay_excepcion_ia(self, _anthropic_mock):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            self.url,
            {"mensaje": "consulta operativa no registrada qwerty personalizada"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["modo"], "segura")


@override_settings(LLM_API_KEY="", GEMINI_API_KEY="", LLM_PROVIDER="gemini")
class ConversacionesAsistentePersistenteTests(APITestCase):
    """Pruebas del historial persistente y aislamiento por usuario."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="residente-chat@test.com",
            password="Segura2026*",
            nombre="Maria",
            apellido="Lopez",
            unidad_residencial="Apto 301 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.otro_usuario = Usuario.objects.create_user(
            email="otro-chat@test.com",
            password="Segura2026*",
            nombre="Pedro",
            apellido="Garcia",
            unidad_residencial="Portería",
            rol=Usuario.Rol.VIGILANTE,
        )
        self.list_url = reverse("asistente:conversacion-list")

    def test_crea_conversacion_y_persiste_mensajes(self):
        self.client.force_authenticate(self.usuario)

        creada = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(creada.status_code, status.HTTP_201_CREATED)

        conversacion_id = creada.data["id"]
        enviada = self.client.post(
            reverse("asistente:conversacion-enviar", kwargs={"pk": conversacion_id}),
            {"mensaje": "¿Cómo reporto un incidente de seguridad?"},
            format="json",
        )

        self.assertEqual(enviada.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(enviada.data["conversacion"]["titulo"], "Nueva conversación")
        self.assertEqual(MensajeAsistente.objects.filter(conversacion_id=conversacion_id).count(), 2)
        self.assertIn("mensaje_usuario", enviada.data)
        self.assertIn("mensaje_asistente", enviada.data)

        mensajes = self.client.get(
            reverse("asistente:conversacion-mensajes", kwargs={"pk": conversacion_id})
        )
        self.assertEqual(mensajes.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mensajes.data), 2)
        self.assertEqual(mensajes.data[0]["rol"], MensajeAsistente.Rol.USUARIO)
        self.assertEqual(mensajes.data[1]["rol"], MensajeAsistente.Rol.ASISTENTE)

    def test_lista_solo_conversaciones_del_usuario_autenticado(self):
        ConversacionAsistente.objects.create(usuario=self.usuario, titulo="Chat propio")
        ConversacionAsistente.objects.create(usuario=self.otro_usuario, titulo="Chat ajeno")

        self.client.force_authenticate(self.usuario)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultados = response.data.get("results", response.data)
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["titulo"], "Chat propio")

    def test_no_permite_acceder_conversaciones_de_otro_usuario(self):
        conversacion = ConversacionAsistente.objects.create(
            usuario=self.usuario,
            titulo="Conversación privada",
        )

        self.client.force_authenticate(self.otro_usuario)
        detalle = self.client.get(
            reverse("asistente:conversacion-detail", kwargs={"pk": conversacion.id})
        )
        eliminar = self.client.delete(
            reverse("asistente:conversacion-detail", kwargs={"pk": conversacion.id})
        )

        self.assertEqual(detalle.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(eliminar.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(ConversacionAsistente.objects.filter(id=conversacion.id).exists())

    def test_eliminar_conversacion_borra_mensajes(self):
        conversacion = ConversacionAsistente.objects.create(usuario=self.usuario, titulo="Temporal")
        MensajeAsistente.objects.create(
            conversacion=conversacion,
            rol=MensajeAsistente.Rol.USUARIO,
            contenido="Hola",
        )

        self.client.force_authenticate(self.usuario)
        response = self.client.delete(
            reverse("asistente:conversacion-detail", kwargs={"pk": conversacion.id})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ConversacionAsistente.objects.filter(id=conversacion.id).exists())
        self.assertEqual(MensajeAsistente.objects.count(), 0)

    def test_rechaza_mensaje_vacio_en_conversacion(self):
        conversacion = ConversacionAsistente.objects.create(usuario=self.usuario, titulo="Validación")

        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            reverse("asistente:conversacion-enviar", kwargs={"pk": conversacion.id}),
            {"mensaje": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
