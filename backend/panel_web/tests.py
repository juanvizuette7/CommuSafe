"""Pruebas del panel web."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from incidentes.models import Incidente


Usuario = get_user_model()


class PanelWebViewsTests(TestCase):
    """Pruebas principales del panel web."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin-panel@test.com",
            password="Admin2026*",
            nombre="Carlos",
            apellido="Admin",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante-panel@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
        )
        self.residente = Usuario.objects.create_user(
            email="residente-panel@test.com",
            password="Commu2026*",
            nombre="María",
            apellido="López",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.incidente = Incidente.objects.create(
            titulo="Prueba panel",
            descripcion="Incidente para probar el panel web.",
            categoria=Incidente.Categoria.SEGURIDAD,
            reportado_por=self.residente,
        )

    def test_login_admin_redirige_al_dashboard(self):
        response = self.client.post(
            reverse("panel_web:login"),
            {"email": self.admin.email, "password": "Admin2026*"},
        )

        self.assertRedirects(response, reverse("panel_web:dashboard"))

    def test_residente_no_puede_entrar_al_panel(self):
        response = self.client.post(
            reverse("panel_web:login"),
            {"email": self.residente.email, "password": "Commu2026*"},
            follow=True,
        )

        self.assertContains(response, "Tu cuenta corresponde a un residente")

    def test_dashboard_requiere_sesion(self):
        response = self.client.get(reverse("panel_web:dashboard"))
        self.assertRedirects(response, f"{reverse('panel_web:login')}?next={reverse('panel_web:dashboard')}")

    def test_cambio_estado_desde_panel_funciona(self):
        self.client.force_login(self.vigilante)

        response = self.client.post(
            reverse("panel_web:incidente_detalle", args=[self.incidente.id]),
            {
                "estado_nuevo": Incidente.Estado.EN_PROCESO,
                "comentario": "Se inicia atención desde el panel.",
            },
            follow=True,
        )

        self.incidente.refresh_from_db()
        self.assertEqual(self.incidente.estado, Incidente.Estado.EN_PROCESO)
        self.assertContains(response, "El incidente fue actualizado correctamente.")
