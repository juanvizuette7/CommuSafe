"""Pruebas del módulo de usuarios."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


Usuario = get_user_model()


class UsuarioModelTests(APITestCase):
    """Pruebas básicas del modelo de usuario."""

    def test_crea_usuario_con_email_normalizado(self):
        usuario = Usuario.objects.create_user(
            email="USUARIO@REMANSOS.COM",
            password="Segura2026*",
            nombre="Laura",
            apellido="Ríos",
            rol=Usuario.Rol.VIGILANTE,
        )

        self.assertEqual(usuario.email, "usuario@remansos.com")


class LoginJWTTests(APITestCase):
    """Pruebas del flujo de autenticación JWT."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="admin@remansos.com",
            password="Admin2026*",
            nombre="Carlos",
            apellido="González",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
        )

    def test_login_devuelve_tokens_y_usuario(self):
        url = reverse("usuarios:login")
        response = self.client.post(
            url,
            {"email": self.usuario.email, "password": "Admin2026*"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["usuario"]["email"], self.usuario.email)
