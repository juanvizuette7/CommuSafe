"""Pruebas del modulo de incidentes."""

from io import BytesIO
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from notificaciones.models import Notificacion

from .models import EvidenciaIncidente, HistorialEstado, Incidente
from .serializers import (
    AgregarEvidenciaSerializer,
    CambiarEstadoSerializer,
    HistorialEstadoSerializer,
    IncidenteCreateSerializer,
    IncidenteListSerializer,
)


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
            descripcion="Se detecto una situacion critica en la porteria.",
            categoria=Incidente.Categoria.EMERGENCIA,
            ubicacion_referencia="Porteria principal",
            reportado_por=self.residente,
        )

        self.assertEqual(incidente.prioridad, Incidente.Prioridad.ALTA)

    def test_prioridad_baja_para_infraestructura(self):
        incidente = Incidente.objects.create(
            titulo="Luz danada",
            descripcion="No funciona una luz del parqueadero.",
            categoria=Incidente.Categoria.INFRAESTRUCTURA,
            reportado_por=self.residente,
        )

        self.assertEqual(incidente.prioridad, Incidente.Prioridad.BAJA)


class IncidenteSerializerTests(APITestCase):
    """Pruebas enfocadas de serializers de incidentes."""

    def setUp(self):
        self.residente = Usuario.objects.create_user(
            email="residente-serializer@test.com",
            password="Segura2026*",
            nombre="Laura",
            apellido="Mora",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante-serializer@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
            unidad_residencial="Porteria",
        )
        self.incidente = Incidente.objects.create(
            titulo="Ruido en zonas comunes",
            descripcion="Reporte para validar serializers.",
            categoria=Incidente.Categoria.CONVIVENCIA,
            reportado_por=self.residente,
        )

    def test_historial_sin_estado_anterior_muestra_label(self):
        historial = HistorialEstado.objects.create(
            incidente=self.incidente,
            estado_anterior="",
            estado_nuevo=Incidente.Estado.REGISTRADO,
            cambiado_por=self.vigilante,
            comentario="Registro inicial.",
        )

        data = HistorialEstadoSerializer(historial).data

        self.assertEqual(data["estado_anterior_label"], "Sin estado previo")

    def test_list_serializer_muestra_nombre_de_usuario_atendedor(self):
        self.incidente.atendido_por = self.vigilante
        self.incidente.total_evidencias = 0

        data = IncidenteListSerializer(self.incidente).data

        self.assertEqual(data["atendido_por_nombre"], self.vigilante.nombre_completo)

    def test_create_serializer_soporta_files_sin_setlist(self):
        class FakeFiles:
            def __bool__(self):
                return True

            def getlist(self, name):
                self.name = name
                return [crear_imagen_prueba("evidencia.png")]

        serializer = IncidenteCreateSerializer(
            context={"request": SimpleNamespace(FILES=FakeFiles())}
        )

        data = serializer.to_internal_value(
            {
                "titulo": "Incidente con evidencia",
                "descripcion": "Valida la rama dict sin setlist.",
                "categoria": Incidente.Categoria.SEGURIDAD,
                "ubicacion_referencia": "Porteria",
            }
        )

        self.assertEqual(len(data["imagenes"]), 1)

    def test_cambiar_estado_rechaza_comentario_corto_y_estado_igual(self):
        request = SimpleNamespace(user=self.vigilante)

        comentario_corto = CambiarEstadoSerializer(
            data={"estado_nuevo": Incidente.Estado.EN_PROCESO, "comentario": "abc"},
            context={"request": request, "incidente": self.incidente},
        )
        self.assertFalse(comentario_corto.is_valid())
        self.assertIn("comentario", comentario_corto.errors)

        mismo_estado = CambiarEstadoSerializer(
            data={"estado_nuevo": Incidente.Estado.REGISTRADO, "comentario": "Mismo estado"},
            context={"request": request, "incidente": self.incidente},
        )
        self.assertFalse(mismo_estado.is_valid())
        self.assertIn("estado_nuevo", mismo_estado.errors)

    def test_agregar_evidencia_rechaza_incidente_cerrado_y_crea_evidencia(self):
        self.incidente.estado = Incidente.Estado.CERRADO
        self.incidente.save(update_fields=["estado"])

        cerrado = AgregarEvidenciaSerializer(
            data={"imagen": crear_imagen_prueba("cerrado.png")},
            context={"incidente": self.incidente},
        )

        self.assertFalse(cerrado.is_valid())
        self.assertIn("imagen", cerrado.errors)

        self.incidente.estado = Incidente.Estado.REGISTRADO
        self.incidente.save(update_fields=["estado"])
        valido = AgregarEvidenciaSerializer(
            data={"imagen": crear_imagen_prueba("valida.png"), "descripcion": "Nueva evidencia"},
            context={"incidente": self.incidente},
        )

        self.assertTrue(valido.is_valid(), valido.errors)
        evidencia = valido.save()
        self.assertEqual(evidencia.incidente, self.incidente)
        self.assertEqual(evidencia.descripcion, "Nueva evidencia")


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
            unidad_residencial="Oficina",
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
            unidad_residencial="Porteria",
        )
        self.residente_1 = Usuario.objects.create_user(
            email="residente1@test.com",
            password="Commu2026*",
            nombre="Maria",
            apellido="Lopez",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.residente_2 = Usuario.objects.create_user(
            email="residente2@test.com",
            password="Commu2026*",
            nombre="Juan",
            apellido="Perez",
            unidad_residencial="Apto 202 Torre B",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.incidente_propio = Incidente.objects.create(
            titulo="Ruido excesivo",
            descripcion="Hay musica alta en la zona social.",
            categoria=Incidente.Categoria.CONVIVENCIA,
            reportado_por=self.residente_1,
        )
        self.incidente_ajeno = Incidente.objects.create(
            titulo="Luz danada",
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
                "descripcion": "No deberia permitir creacion desde administrador.",
                "categoria": Incidente.Categoria.SEGURIDAD,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vigilante_si_puede_crear_incidentes(self):
        self.client.force_authenticate(self.vigilante)

        response = self.client.post(
            reverse("incidentes:incidente-list"),
            {
                "titulo": "Puerta abierta",
                "descripcion": "Se detecto puerta de acceso abierta sin control.",
                "categoria": Incidente.Categoria.SEGURIDAD,
                "ubicacion_referencia": "Entrada principal",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["reportado_por"]["id"], str(self.vigilante.id))

    def test_crear_incidente_con_evidencias(self):
        self.client.force_authenticate(self.residente_1)
        url = reverse("incidentes:incidente-list")

        response = self.client.post(
            url,
            {
                "titulo": "Persona sospechosa",
                "descripcion": "Se observa una persona desconocida en la entrada.",
                "categoria": Incidente.Categoria.SEGURIDAD,
                "ubicacion_referencia": "Porteria",
                "imagenes": [crear_imagen_prueba("uno.png"), crear_imagen_prueba("dos.png")],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["evidencias"]), 2)
        self.assertEqual(response.data["prioridad"], Incidente.Prioridad.ALTA)

    def test_no_permite_crear_incidente_con_mas_de_tres_evidencias(self):
        self.client.force_authenticate(self.residente_1)

        response = self.client.post(
            reverse("incidentes:incidente-list"),
            {
                "titulo": "Prueba evidencias",
                "descripcion": "Demasiadas evidencias para validar limite.",
                "categoria": Incidente.Categoria.SEGURIDAD,
                "imagenes": [
                    crear_imagen_prueba("1.png"),
                    crear_imagen_prueba("2.png"),
                    crear_imagen_prueba("3.png"),
                    crear_imagen_prueba("4.png"),
                ],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("imagenes", response.data)

    def test_cambiar_estado_crea_historial_y_notificacion(self):
        self.client.force_authenticate(self.vigilante)
        url = reverse("incidentes:incidente-cambiar-estado", args=[self.incidente_propio.id])

        response = self.client.post(
            url,
            {
                "estado_nuevo": Incidente.Estado.EN_PROCESO,
                "comentario": "El equipo de vigilancia ya esta atendiendo el caso.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.incidente_propio.refresh_from_db()
        self.assertEqual(self.incidente_propio.estado, Incidente.Estado.EN_PROCESO)
        self.assertEqual(self.incidente_propio.atendido_por, self.vigilante)
        self.assertEqual(HistorialEstado.objects.filter(incidente=self.incidente_propio).count(), 1)
        self.assertEqual(Notificacion.objects.filter(destinatario=self.residente_1).count(), 1)

    def test_residente_no_puede_cambiar_estado(self):
        self.client.force_authenticate(self.residente_1)

        response = self.client.post(
            reverse("incidentes:incidente-cambiar-estado", args=[self.incidente_propio.id]),
            {
                "estado_nuevo": Incidente.Estado.EN_PROCESO,
                "comentario": "Intento no permitido",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_permite_transicion_invalida(self):
        self.client.force_authenticate(self.vigilante)

        response = self.client.post(
            reverse("incidentes:incidente-cambiar-estado", args=[self.incidente_propio.id]),
            {
                "estado_nuevo": Incidente.Estado.RESUELTO,
                "comentario": "No deberia saltar estados",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estado_nuevo", response.data)

    def test_vigilante_no_puede_cerrar_incidente(self):
        self.incidente_propio.estado = Incidente.Estado.RESUELTO
        self.incidente_propio.save(update_fields=["estado"])
        self.client.force_authenticate(self.vigilante)

        response = self.client.post(
            reverse("incidentes:incidente-cambiar-estado", args=[self.incidente_propio.id]),
            {
                "estado_nuevo": Incidente.Estado.CERRADO,
                "comentario": "Intento de cierre sin rol admin",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estado_nuevo", response.data)

    def test_admin_puede_cerrar_incidente_resuelto(self):
        self.incidente_propio.estado = Incidente.Estado.RESUELTO
        self.incidente_propio.atendido_por = self.vigilante
        self.incidente_propio.save(update_fields=["estado", "atendido_por"])
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("incidentes:incidente-cambiar-estado", args=[self.incidente_propio.id]),
            {
                "estado_nuevo": Incidente.Estado.CERRADO,
                "comentario": "Cierre administrativo final.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.incidente_propio.refresh_from_db()
        self.assertEqual(self.incidente_propio.estado, Incidente.Estado.CERRADO)
        self.assertIsNotNone(self.incidente_propio.fecha_cierre)
        self.assertEqual(self.incidente_propio.observaciones_cierre, "Cierre administrativo final.")

    def test_agregar_evidencia_de_incidente_ajeno_devuelve_404_para_residente(self):
        self.client.force_authenticate(self.residente_1)

        response = self.client.post(
            reverse("incidentes:incidente-agregar-evidencia", args=[self.incidente_ajeno.id]),
            {"imagen": crear_imagen_prueba("extra.png"), "descripcion": "No deberia poder"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agregar_evidencia_limite_tres_por_incidente(self):
        EvidenciaIncidente.objects.create(incidente=self.incidente_propio, imagen=crear_imagen_prueba("a.png"))
        EvidenciaIncidente.objects.create(incidente=self.incidente_propio, imagen=crear_imagen_prueba("b.png"))
        EvidenciaIncidente.objects.create(incidente=self.incidente_propio, imagen=crear_imagen_prueba("c.png"))
        self.client.force_authenticate(self.residente_1)

        response = self.client.post(
            reverse("incidentes:incidente-agregar-evidencia", args=[self.incidente_propio.id]),
            {"imagen": crear_imagen_prueba("d.png"), "descripcion": "Cuarta evidencia"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("imagen", response.data)

    def test_ordenamiento_por_prioridad_descendente(self):
        self.client.force_authenticate(self.admin)
        Incidente.objects.create(
            titulo="Emergencia urgente",
            descripcion="Caso critico",
            categoria=Incidente.Categoria.EMERGENCIA,
            reportado_por=self.residente_1,
        )

        response = self.client.get(reverse("incidentes:incidente-list"), {"ordering": "-prioridad"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prioridades = [item["prioridad"] for item in response.data["results"]]
        self.assertEqual(prioridades[0], Incidente.Prioridad.ALTA)

    def test_busqueda_por_titulo(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse("incidentes:incidente-list"), {"search": "Ruido"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.incidente_propio.id))

    def test_destroy_solo_admin(self):
        self.client.force_authenticate(self.vigilante)

        response = self.client.delete(reverse("incidentes:incidente-detail", args=[self.incidente_propio.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
