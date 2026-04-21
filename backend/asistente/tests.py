"""Pruebas del módulo de asistente virtual."""

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


Usuario = get_user_model()


class ChatAsistenteFallbackTests(APITestCase):
    """Pruebas del fallback del asistente."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="asistente@test.com",
            password="Segura2026*",
            nombre="Laura",
            apellido="Ríos",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.client.force_authenticate(self.usuario)

    @override_settings(LLM_API_KEY="")
    def test_responde_con_fallback_para_horarios(self):
        response = self.client.post(
            reverse("asistente:chat"),
            {
                "mensaje": "¿Cuál es el horario de las áreas comunes?",
                "historial": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["modo"], "fallback")
        self.assertIn("áreas comunes", response.data["respuesta"].lower())

    @override_settings(LLM_API_KEY="")
    def test_limita_historial_a_ultimos_ocho_mensajes(self):
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
