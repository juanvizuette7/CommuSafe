"""Pruebas del módulo de incidentes."""

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from notificaciones.models import Notificacion

from .models import HistorialEstado, Incidente


Usuario = get_user_model()


def crear_imagen_prueba(nombre="prueba.png", color=(15, 52, 96)):
    archivo = BytesIO()
    imagen = Image.new("RGB", (60, 60), color=color)
    imagen.save(archivo, format="PNG")
    archivo.seek(0)
    return SimpleUploadedFile(nombre, archivo.read(), content_type="image/png")


class IncidenteModelTests(APITestCase):
    """Pruebas del modelo Incidente."""

    def setUp(self):
        self.residente = Usuario.objects.create_user(
            email="residente@test.com",
            password="Segura2026*",
            nombre="Laura",
            apellido="Mora",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )

    def test_prioridad_se_calcula_automaticamente(self):
        incidente = Incidente.objects.create(
            titulo="Alarma de emergencia",
            descripcion="Se detectó una situación crítica en la portería.",
            categoria=Incidente.Categoria.EMERGENCIA,
            ubicacion_referencia="Portería principal",
            reportado_por=self.residente,
        )

        self.assertEqual(incidente.prioridad, Incidente.Prioridad.ALTA)


class IncidenteAPITests(APITestCase):
    """Pruebas del API de incidentes."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin@test.com",
            password="Admin2026*",
            nombre="Carlos",
            apellido="Admin",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
        )
        self.residente_1 = Usuario.objects.create_user(
            email="residente1@test.com",
            password="Commu2026*",
            nombre="María",
            apellido="López",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.residente_2 = Usuario.objects.create_user(
            email="residente2@test.com",
            password="Commu2026*",
            nombre="Juan",
            apellido="Pérez",
            unidad_residencial="Apto 202 Torre B",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.incidente_propio = Incidente.objects.create(
            titulo="Ruido excesivo",
            descripcion="Hay música alta en la zona social.",
            categoria=Incidente.Categoria.CONVIVENCIA,
            reportado_por=self.residente_1,
        )
        self.incidente_ajeno = Incidente.objects.create(
            titulo="Luz dañada",
            descripcion="La luminaria del parqueadero no funciona.",
            categoria=Incidente.Categoria.INFRAESTRUCTURA,
            reportado_por=self.residente_2,
        )

    def test_residente_solo_ve_sus_propios_incidentes(self):
        self.client.force_authenticate(self.residente_1)

        response = self.client.get(reverse("incidentes:incidente-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.incidente_propio.id))

    def test_administrador_no_puede_crear_incidentes(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("incidentes:incidente-list"),
            {
                "titulo": "Prueba",
                "descripcion": "No debería permitir creación desde administrador.",
                "categoria": Incidente.Categoria.SEGURIDAD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_crear_incidente_con_evidencias(self):
        self.client.force_authenticate(self.residente_1)
        url = reverse("incidentes:incidente-list")

        response = self.client.post(
            url,
            {
                "titulo": "Persona sospechosa",
                "descripcion": "Se observa una persona desconocida en la entrada.",
                "categoria": Incidente.Categoria.SEGURIDAD,
                "ubicacion_referencia": "Portería",
                "imagenes": [crear_imagen_prueba("uno.png"), crear_imagen_prueba("dos.png")],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["evidencias"]), 2)
        self.assertEqual(response.data["prioridad"], Incidente.Prioridad.ALTA)

    def test_cambiar_estado_crea_historial_y_notificacion(self):
        self.client.force_authenticate(self.vigilante)
        url = reverse("incidentes:incidente-cambiar-estado", args=[self.incidente_propio.id])

        response = self.client.post(
            url,
            {
                "estado_nuevo": Incidente.Estado.EN_PROCESO,
                "comentario": "El equipo de vigilancia ya está atendiendo el caso.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.incidente_propio.refresh_from_db()
        self.assertEqual(self.incidente_propio.estado, Incidente.Estado.EN_PROCESO)
        self.assertEqual(self.incidente_propio.atendido_por, self.vigilante)
        self.assertEqual(HistorialEstado.objects.filter(incidente=self.incidente_propio).count(), 1)
        self.assertEqual(Notificacion.objects.filter(usuario=self.residente_1).count(), 1)
