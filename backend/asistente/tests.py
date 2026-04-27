"""Pruebas del modulo de asistente virtual."""

from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .views import _api_llm_configurada, _extraer_texto_anthropic, _normalizar_historial, _respuesta_fallback


Usuario = get_user_model()


@override_settings(LLM_API_KEY="", GEMINI_API_KEY="", LLM_PROVIDER="gemini")
class ChatAsistenteFallbackTests(APITestCase):
    """Pruebas del fallback del asistente."""

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
        self.assertEqual(response.data["modo"], "fallback")
        self.assertIn("areas comunes", response.data["respuesta"].lower())

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
        self.assertEqual(response.data["modo"], "fallback")

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
        self.assertIn("administracion", response.data["respuesta"].lower())

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
        self.assertEqual(response.data["modo"], "fallback")

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

        self.assertIn("cuotas", cuotas.data["respuesta"].lower())
        self.assertIn("convivencia", normas.data["respuesta"].lower())
        self.assertIn("reportar incidentes", app.data["respuesta"].lower())

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
            self.assertTrue(_api_llm_configurada())

    def test_normalizar_historial(self):
        historial = [
            {"rol": "usuario", "contenido": " Hola "},
            {"rol": "asistente", "contenido": " Mundo "},
        ]

        normalizado = _normalizar_historial(historial)

        self.assertEqual(normalizado[0], {"role": "user", "content": "Hola"})
        self.assertEqual(normalizado[1], {"role": "assistant", "content": "Mundo"})

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
        self.assertIn("No tengo una respuesta", texto)


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
    @patch("asistente.views.Anthropic")
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
                "mensaje": "Dame un resumen",
                "historial": [{"rol": "usuario", "contenido": "hola"}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["modo"], "ia")
        self.assertIn("Respuesta IA", response.data["respuesta"])

    @override_settings(LLM_API_KEY="clave-real")
    @patch("asistente.views.Anthropic")
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
            {"mensaje": "Necesito ayuda con convivencia"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["modo"], "fallback")

    @override_settings(LLM_API_KEY="clave-real")
    @patch("asistente.views.Anthropic", side_effect=Exception("fallo"))
    def test_modo_fallback_si_hay_excepcion_ia(self, _anthropic_mock):
        self.client.force_authenticate(self.usuario)
        response = self.client.post(
            self.url,
            {"mensaje": "Necesito ayuda"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["modo"], "fallback")
