"""Pruebas del modulo de notificaciones."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from incidentes.models import Incidente

from .models import Notificacion
from .services import (
    _configuracion_push_disponible,
    _crear_registro_y_enviar_push,
    _intentar_enviar_push,
    notificar_aviso_admin,
    notificar_cambio_estado,
    notificar_incidente_nuevo,
)


Usuario = get_user_model()


class NotificacionServicesTests(APITestCase):
    """Pruebas de servicios de notificacion."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin-noti@test.com",
            password="Admin2026*",
            nombre="Carlos",
            apellido="Admin",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            unidad_residencial="Oficina",
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante-noti@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
            unidad_residencial="Porteria",
        )
        self.residente_1 = Usuario.objects.create_user(
            email="residente-noti1@test.com",
            password="Commu2026*",
            nombre="Maria",
            apellido="Lopez",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.residente_2 = Usuario.objects.create_user(
            email="residente-noti2@test.com",
            password="Commu2026*",
            nombre="Juan",
            apellido="Perez",
            unidad_residencial="Apto 202 Torre B",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.incidente = Incidente.objects.create(
            titulo="Emergencia en porteria",
            descripcion="Se reporta una situacion critica.",
            categoria=Incidente.Categoria.EMERGENCIA,
            reportado_por=self.residente_1,
        )

    def test_notificar_incidente_nuevo_segmenta_por_rol(self):
        notificar_incidente_nuevo(self.incidente)

        destinatarios = set(Notificacion.objects.values_list("destinatario__email", flat=True))
        self.assertIn(self.admin.email, destinatarios)
        self.assertIn(self.vigilante.email, destinatarios)
        self.assertIn(self.residente_2.email, destinatarios)
        self.assertNotIn(self.residente_1.email, destinatarios)

    def test_notificar_incidente_alta_usa_tipo_emergencia(self):
        notificar_incidente_nuevo(self.incidente)

        tipos = set(Notificacion.objects.values_list("tipo", flat=True))
        self.assertEqual(tipos, {Notificacion.Tipo.EMERGENCIA})

    def test_notificar_incidente_baja_no_notifica_residentes_ajenos(self):
        incidente_bajo = Incidente.objects.create(
            titulo="Arreglo luminaria",
            descripcion="Caso no critico de infraestructura.",
            categoria=Incidente.Categoria.INFRAESTRUCTURA,
            reportado_por=self.residente_1,
        )

        notificar_incidente_nuevo(incidente_bajo)

        destinatarios = set(
            Notificacion.objects.filter(incidente_relacionado=incidente_bajo).values_list(
                "destinatario__email", flat=True
            )
        )
        self.assertIn(self.admin.email, destinatarios)
        self.assertIn(self.vigilante.email, destinatarios)
        self.assertNotIn(self.residente_2.email, destinatarios)

    def test_notificar_cambio_estado_usa_tipo_correcto(self):
        self.incidente.atendido_por = self.vigilante
        self.incidente.estado = Incidente.Estado.EN_PROCESO
        self.incidente.save()

        notificar_cambio_estado(self.incidente, Incidente.Estado.EN_PROCESO)

        self.assertEqual(
            Notificacion.objects.filter(tipo=Notificacion.Tipo.CAMBIO_ESTADO).count(),
            2,
        )

    def test_notificar_cambio_estado_omite_destinatario_inactivo(self):
        self.vigilante.activo = False
        self.vigilante.save(update_fields=["activo"])
        self.incidente.atendido_por = self.vigilante
        self.incidente.save(update_fields=["atendido_por"])

        notificar_cambio_estado(self.incidente, Incidente.Estado.EN_PROCESO)

        destinatarios = set(Notificacion.objects.values_list("destinatario_id", flat=True))
        self.assertIn(self.residente_1.id, destinatarios)
        self.assertNotIn(self.vigilante.id, destinatarios)

    def test_notificar_aviso_admin_notifica_a_todos_los_activos(self):
        notificar_aviso_admin("Mantenimiento programado", "Habra suspension temporal de energia.")

        self.assertEqual(Notificacion.objects.filter(tipo=Notificacion.Tipo.AVISO_ADMIN).count(), 4)

    def test_configuracion_push_disponible_valida_dependencia_clave_y_archivo(self):
        with patch("notificaciones.services.FCMNotification", None):
            self.assertFalse(_configuracion_push_disponible())

        with override_settings(FCM_SERVER_KEY="REEMPLAZAR"):
            self.assertFalse(_configuracion_push_disponible())

        with override_settings(FCM_SERVER_KEY="credenciales-fcm.json"):
            with patch("notificaciones.services.os.path.exists", return_value=True):
                self.assertTrue(_configuracion_push_disponible())

    def test_crear_registro_marca_push_enviado_si_fcm_responde(self):
        self.residente_1.fcm_token = "token-fcm-valido"
        self.residente_1.save(update_fields=["fcm_token"])
        cliente = Mock()

        with override_settings(FCM_SERVER_KEY="credenciales-fcm.json"):
            with patch("notificaciones.services.os.path.exists", return_value=True):
                with patch("notificaciones.services.FCMNotification", return_value=cliente):
                    notificacion = _crear_registro_y_enviar_push(
                        destinatario=self.residente_1,
                        titulo="Titulo push",
                        cuerpo="Cuerpo push",
                        tipo=Notificacion.Tipo.AVISO_ADMIN,
                        incidente_relacionado=self.incidente,
                    )

        self.assertTrue(notificacion.enviada_push)
        cliente.notify.assert_called_once()
        payload = cliente.notify.call_args.kwargs["data_payload"]
        self.assertEqual(payload["incidente_id"], str(self.incidente.id))

    def test_intentar_enviar_push_atrapa_error_del_proveedor(self):
        self.residente_1.fcm_token = "token-fcm-error"
        self.residente_1.save(update_fields=["fcm_token"])
        cliente = Mock()
        cliente.notify.side_effect = RuntimeError("FCM no disponible")

        with override_settings(FCM_SERVER_KEY="credenciales-fcm.json"):
            with patch("notificaciones.services.os.path.exists", return_value=True):
                with patch("notificaciones.services.FCMNotification", return_value=cliente):
                    with self.assertLogs("notificaciones.services", level="WARNING"):
                        enviado = _intentar_enviar_push(
                            usuario=self.residente_1,
                            titulo="Titulo push",
                            cuerpo="Cuerpo push",
                            incidente=self.incidente,
                        )

        self.assertFalse(enviado)

    def test_notificar_incidente_nuevo_omite_destinatarios_duplicados(self):
        class FakeQuerySet(list):
            def exclude(self, **kwargs):
                return self

            def distinct(self):
                return self

        incidente = SimpleNamespace(
            reportado_por_id=self.residente_1.id,
            prioridad=Incidente.Prioridad.ALTA,
            Prioridad=Incidente.Prioridad,
            titulo="Incidente duplicado",
            get_categoria_display=lambda: "Seguridad",
            get_prioridad_display=lambda: "Alta",
        )

        with patch(
            "notificaciones.services.Usuario.objects.filter",
            side_effect=[FakeQuerySet([self.admin]), FakeQuerySet([self.admin])],
        ):
            with patch("notificaciones.services._crear_registro_y_enviar_push") as crear_mock:
                notificar_incidente_nuevo(incidente)

        crear_mock.assert_called_once()


class NotificacionViewSetTests(APITestCase):
    """Pruebas de endpoints de notificaciones."""

    def setUp(self):
        self.residente = Usuario.objects.create_user(
            email="residente-view@test.com",
            password="Commu2026*",
            nombre="Laura",
            apellido="Rios",
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
            leida=False,
        )
        Notificacion.objects.create(
            destinatario=self.residente,
            titulo="Segunda",
            cuerpo="Contenido dos",
            tipo=Notificacion.Tipo.AVISO_ADMIN,
            leida=False,
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
        self.assertEqual(response.data["count"], 2)

    def test_no_leidas_count(self):
        self.client.force_authenticate(self.residente)

        response = self.client.get(reverse("notificaciones:notificacion-no-leidas-count"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["no_leidas"], 2)

    def test_marcar_como_leida(self):
        self.client.force_authenticate(self.residente)

        response = self.client.post(reverse("notificaciones:notificacion-leer", args=[self.notificacion.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notificacion.refresh_from_db()
        self.assertTrue(self.notificacion.leida)

    def test_leer_todas(self):
        self.client.force_authenticate(self.residente)

        response = self.client.post(reverse("notificaciones:notificacion-leer-todas"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_actualizadas"], 2)
        self.assertEqual(Notificacion.objects.filter(destinatario=self.residente, leida=False).count(), 0)

    def test_endpoint_requiere_autenticacion(self):
        response = self.client.get(reverse("notificaciones:notificacion-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
