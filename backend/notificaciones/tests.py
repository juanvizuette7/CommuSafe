"""Pruebas del módulo de notificaciones."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from incidentes.models import Incidente

from .models import Notificacion


Usuario = get_user_model()


class NotificacionModelTests(TestCase):
    """Pruebas básicas del modelo de notificación."""

    def setUp(self):
        self.residente = Usuario.objects.create_user(
            email="noti@test.com",
            password="Segura2026*",
            nombre="Laura",
            apellido="Ríos",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.incidente = Incidente.objects.create(
            titulo="Prueba notificación",
            descripcion="Incidente para validar la relación con notificaciones.",
            categoria=Incidente.Categoria.SEGURIDAD,
            reportado_por=self.residente,
        )

    def test_crea_notificacion_asociada_a_incidente(self):
        notificacion = Notificacion.objects.create(
            usuario=self.residente,
            incidente=self.incidente,
            titulo="Cambio de estado",
            mensaje="Tu incidente cambió de estado.",
        )

        self.assertEqual(notificacion.usuario, self.residente)
        self.assertEqual(notificacion.incidente, self.incidente)
