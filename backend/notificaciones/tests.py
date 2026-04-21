"""Pruebas del módulo de notificaciones."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from incidentes.models import Incidente

from .models import Notificacion
from .services import notificar_aviso_admin, notificar_cambio_estado, notificar_incidente_nuevo


Usuario = get_user_model()


class NotificacionServicesTests(APITestCase):
    """Pruebas de servicios de notificación."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin-noti@test.com",
            password="Admin2026*",
            nombre="Carlos",
            apellido="Admin",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante-noti@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
        )
        self.residente_1 = Usuario.objects.create_user(
            email="residente-noti1@test.com",
            password="Commu2026*",
            nombre="María",
            apellido="López",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.residente_2 = Usuario.objects.create_user(
            email="residente-noti2@test.com",
            password="Commu2026*",
            nombre="Juan",
            apellido="Pérez",
            unidad_residencial="Apto 202 Torre B",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.incidente = Incidente.objects.create(
            titulo="Emergencia en portería",
            descripcion="Se reporta una situación crítica.",
            categoria=Incidente.Categoria.EMERGENCIA,
            reportado_por=self.residente_1,
        )

    def test_notificar_incidente_nuevo_segmenta_por_rol(self):
        notificar_incidente_nuevo(self.incidente)

        destinatarios = set(
            Notificacion.objects.values_list("destinatario__email", flat=True)
        )
        self.assertIn(self.admin.email, destinatarios)
        self.assertIn(self.vigilante.email, destinatarios)
        self.assertIn(self.residente_2.email, destinatarios)
        self.assertNotIn(self.residente_1.email, destinatarios)

    def test_notificar_cambio_estado_usa_tipo_correcto(self):
        self.incidente.atendido_por = self.vigilante
        self.incidente.estado = Incidente.Estado.EN_PROCESO
        self.incidente.save()

        notificar_cambio_estado(self.incidente, Incidente.Estado.EN_PROCESO)

        self.assertEqual(Notificacion.objects.filter(tipo=Notificacion.Tipo.CAMBIO_ESTADO).count(), 2)

    def test_notificar_aviso_admin_notifica_a_todos_los_activos(self):
        notificar_aviso_admin("Mantenimiento programado", "Habrá suspensión temporal de energía.")

        self.assertEqual(Notificacion.objects.filter(tipo=Notificacion.Tipo.AVISO_ADMIN).count(), 4)


class NotificacionViewSetTests(APITestCase):
    """Pruebas de endpoints de notificaciones."""

    def setUp(self):
        self.residente = Usuario.objects.create_user(
            email="residente-view@test.com",
            password="Commu2026*",
            nombre="Laura",
            apellido="Ríos",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.otro = Usuario.objects.create_user(
            email="otro-view@test.com",
            password="Commu2026*",
            nombre="Diana",
            apellido="Mora",
            unidad_residencial="Apto 202 Torre B",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.notificacion = Notificacion.objects.create(
            destinatario=self.residente,
            titulo="Prueba",
            cuerpo="Contenido",
            tipo=Notificacion.Tipo.AVISO_ADMIN,
        )
        Notificacion.objects.create(
            destinatario=self.otro,
            titulo="Privada",
            cuerpo="Solo para otra residente",
            tipo=Notificacion.Tipo.AVISO_ADMIN,
        )

    def test_usuario_solo_ve_sus_notificaciones(self):
        self.client.force_authenticate(self.residente)

        response = self.client.get(reverse("notificaciones:notificacion-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_marcar_como_leida(self):
        self.client.force_authenticate(self.residente)

        response = self.client.post(
            reverse("notificaciones:notificacion-leer", args=[self.notificacion.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notificacion.refresh_from_db()
        self.assertTrue(self.notificacion.leida)
