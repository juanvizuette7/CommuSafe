from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from incidentes.models import EvidenciaIncidente, HistorialEstado, Incidente, IncidenteEliminado
from notificaciones.models import Notificacion


pytestmark = pytest.mark.django_db

Usuario = get_user_model()


def crear_usuario(email, rol=Usuario.Rol.RESIDENTE, password="Commu2026*", **extra):
    defaults = {
        "nombre": extra.pop("nombre", "Usuario"),
        "apellido": extra.pop("apellido", rol.title()),
        "rol": rol,
        "unidad_residencial": extra.pop("unidad_residencial", "Apto 101 Torre A"),
    }
    if rol != Usuario.Rol.RESIDENTE:
        defaults["unidad_residencial"] = extra.pop("unidad_residencial", "")
    defaults.update(extra)
    return Usuario.objects.create_user(email=email, password=password, **defaults)


def cliente_autenticado(usuario):
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente


def imagen_prueba(nombre="evidencia.jpg"):
    return SimpleUploadedFile(
        nombre,
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
        b"\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00"
        b"\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
        content_type="image/gif",
    )


class TestAutenticacion:
    def test_login_correcto_devuelve_tokens_y_usuario(self):
        crear_usuario(
            "residente-login@test.com",
            nombre="Maria",
            apellido="Lopez",
            password="Commu2026*",
        )
        cliente = APIClient()

        respuesta = cliente.post(
            "/api/auth/login/",
            {"email": "residente-login@test.com", "password": "Commu2026*"},
            format="json",
        )

        assert respuesta.status_code == 200
        assert respuesta.data["access"]
        assert respuesta.data["refresh"]
        assert respuesta.data["usuario"]["email"] == "residente-login@test.com"
        assert respuesta.data["usuario"]["rol"] == Usuario.Rol.RESIDENTE

    def test_login_incorrecto_devuelve_401(self):
        crear_usuario("residente-error@test.com", password="Commu2026*")
        cliente = APIClient()

        respuesta = cliente.post(
            "/api/auth/login/",
            {"email": "residente-error@test.com", "password": "ClaveIncorrecta"},
            format="json",
        )

        assert respuesta.status_code == 401

    def test_endpoint_protegido_rechaza_request_sin_token(self):
        cliente = APIClient()

        respuesta = cliente.get("/api/auth/perfil/")

        assert respuesta.status_code == 401

    def test_refresh_token_funciona(self):
        crear_usuario("residente-refresh@test.com", password="Commu2026*")
        cliente = APIClient()
        login = cliente.post(
            "/api/auth/login/",
            {"email": "residente-refresh@test.com", "password": "Commu2026*"},
            format="json",
        )

        respuesta = cliente.post(
            "/api/auth/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
        )

        assert respuesta.status_code == 200
        assert respuesta.data["access"]


class TestControlAcceso:
    def test_residente_no_accede_a_endpoints_de_administracion(self):
        residente = crear_usuario("residente-admin-denegado@test.com")
        cliente = cliente_autenticado(residente)

        respuesta = cliente.get("/api/auth/usuarios/")

        assert respuesta.status_code == 403

    def test_vigilante_ve_todos_los_incidentes(self):
        vigilante = crear_usuario(
            "vigilante-lista@test.com",
            rol=Usuario.Rol.VIGILANTE,
            nombre="Pedro",
            apellido="Garcia",
        )
        residente_uno = crear_usuario("residente-lista1@test.com")
        residente_dos = crear_usuario(
            "residente-lista2@test.com",
            unidad_residencial="Apto 202 Torre B",
        )
        Incidente.objects.create(
            titulo="Caso visible uno",
            descripcion="Incidente reportado por residente uno.",
            categoria=Incidente.Categoria.SEGURIDAD,
            reportado_por=residente_uno,
        )
        Incidente.objects.create(
            titulo="Caso visible dos",
            descripcion="Incidente reportado por residente dos.",
            categoria=Incidente.Categoria.CONVIVENCIA,
            reportado_por=residente_dos,
        )
        cliente = cliente_autenticado(vigilante)

        respuesta = cliente.get("/api/incidentes/")

        assert respuesta.status_code == 200
        assert respuesta.data["count"] == 2

    def test_residente_solo_ve_sus_propios_incidentes(self):
        residente = crear_usuario("residente-propios@test.com")
        otro = crear_usuario("residente-ajeno@test.com", unidad_residencial="Apto 303 Torre C")
        Incidente.objects.create(
            titulo="Propio",
            descripcion="Incidente propio del residente autenticado.",
            categoria=Incidente.Categoria.CONVIVENCIA,
            reportado_por=residente,
        )
        Incidente.objects.create(
            titulo="Ajeno",
            descripcion="Incidente de otro residente.",
            categoria=Incidente.Categoria.SEGURIDAD,
            reportado_por=otro,
        )
        cliente = cliente_autenticado(residente)

        respuesta = cliente.get("/api/incidentes/")

        assert respuesta.status_code == 200
        assert respuesta.data["count"] == 1
        assert respuesta.data["results"][0]["titulo"] == "Propio"

    def test_solo_administrador_puede_eliminar_incidentes(self):
        residente = crear_usuario("residente-delete@test.com")
        vigilante = crear_usuario(
            "vigilante-delete@test.com",
            rol=Usuario.Rol.VIGILANTE,
            nombre="Luis",
            apellido="Martinez",
        )
        admin = crear_usuario(
            "admin-delete@test.com",
            rol=Usuario.Rol.ADMINISTRADOR,
            password="Admin2026*",
            nombre="Carlos",
            apellido="Gonzalez",
            is_staff=True,
        )
        incidente = Incidente.objects.create(
            titulo="Incidente para eliminar",
            descripcion="Debe ser eliminado solo por administrador.",
            categoria=Incidente.Categoria.INFRAESTRUCTURA,
            reportado_por=residente,
        )

        respuesta_vigilante = cliente_autenticado(vigilante).delete(
            f"/api/incidentes/{incidente.id}/"
        )
        respuesta_admin_sin_motivo = cliente_autenticado(admin).delete(
            f"/api/incidentes/{incidente.id}/"
        )
        respuesta_admin = cliente_autenticado(admin).delete(
            f"/api/incidentes/{incidente.id}/",
            {"motivo": "Motivo de auditoria suficientemente claro."},
            format="json",
        )

        assert respuesta_vigilante.status_code == 403
        assert respuesta_admin_sin_motivo.status_code == 400
        assert respuesta_admin.status_code == 200
        assert not Incidente.objects.filter(id=incidente.id).exists()
        assert IncidenteEliminado.objects.filter(
            incidente_id=incidente.id,
            eliminado_por=admin,
            titulo="Incidente para eliminar",
        ).exists()


class TestLogicaIncidentes:
    @pytest.mark.parametrize(
        ("categoria", "prioridad"),
        [
            (Incidente.Categoria.EMERGENCIA, Incidente.Prioridad.ALTA),
            (Incidente.Categoria.SEGURIDAD, Incidente.Prioridad.ALTA),
            (Incidente.Categoria.CONVIVENCIA, Incidente.Prioridad.MEDIA),
            (Incidente.Categoria.INFRAESTRUCTURA, Incidente.Prioridad.BAJA),
        ],
    )
    def test_prioridad_se_calcula_automaticamente_por_categoria(self, categoria, prioridad):
        residente = crear_usuario(f"residente-{categoria.lower()}@test.com")

        incidente = Incidente.objects.create(
            titulo=f"Incidente {categoria}",
            descripcion="Descripcion suficientemente clara para la prueba.",
            categoria=categoria,
            reportado_por=residente,
        )

        assert incidente.prioridad == prioridad

    def test_cambiar_estado_crea_registro_de_historial(self):
        vigilante = crear_usuario(
            "vigilante-historial@test.com",
            rol=Usuario.Rol.VIGILANTE,
            nombre="Pedro",
            apellido="Garcia",
        )
        residente = crear_usuario("residente-historial@test.com")
        incidente = Incidente.objects.create(
            titulo="Cambio de estado trazable",
            descripcion="El cambio debe quedar registrado en historial.",
            categoria=Incidente.Categoria.SEGURIDAD,
            reportado_por=residente,
        )
        cliente = cliente_autenticado(vigilante)

        respuesta = cliente.post(
            f"/api/incidentes/{incidente.id}/cambiar-estado/",
            {
                "estado_nuevo": Incidente.Estado.EN_PROCESO,
                "comentario": "Vigilancia atiende el caso.",
            },
            format="json",
        )

        assert respuesta.status_code == 200
        assert HistorialEstado.objects.filter(
            incidente=incidente,
            estado_anterior=Incidente.Estado.REGISTRADO,
            estado_nuevo=Incidente.Estado.EN_PROCESO,
            cambiado_por=vigilante,
        ).exists()

    def test_no_se_pueden_subir_mas_de_tres_evidencias_por_incidente(self, tmp_path, settings):
        settings.MEDIA_ROOT = tmp_path
        residente = crear_usuario("residente-evidencias@test.com")
        incidente = Incidente.objects.create(
            titulo="Incidente con evidencias completas",
            descripcion="Ya tiene tres evidencias cargadas.",
            categoria=Incidente.Categoria.INFRAESTRUCTURA,
            reportado_por=residente,
        )
        for indice in range(3):
            EvidenciaIncidente.objects.create(
                incidente=incidente,
                imagen=imagen_prueba(f"evidencia-{indice}.gif"),
            )
        cliente = cliente_autenticado(residente)

        respuesta = cliente.post(
            f"/api/incidentes/{incidente.id}/agregar-evidencia/",
            {"imagen": imagen_prueba("cuarta.gif")},
            format="multipart",
        )

        assert respuesta.status_code == 400
        assert incidente.evidencias.count() == 3


class TestNotificaciones:
    def test_incidente_prioridad_alta_notifica_a_todos_los_usuarios_activos(self):
        admin = crear_usuario(
            "admin-noti-alta@test.com",
            rol=Usuario.Rol.ADMINISTRADOR,
            password="Admin2026*",
            is_staff=True,
        )
        vigilante = crear_usuario(
            "vigilante-noti-alta@test.com",
            rol=Usuario.Rol.VIGILANTE,
            nombre="Pedro",
            apellido="Garcia",
        )
        reportante = crear_usuario("residente-reportante-alta@test.com")
        residente_ajeno = crear_usuario(
            "residente-ajeno-alta@test.com",
            unidad_residencial="Apto 404 Torre D",
        )
        cliente = cliente_autenticado(reportante)

        respuesta = cliente.post(
            "/api/incidentes/",
            {
                "titulo": "Emergencia comunitaria",
                "descripcion": "Situacion urgente que debe ser conocida por todos.",
                "categoria": Incidente.Categoria.EMERGENCIA,
                "ubicacion_referencia": "Porteria principal",
            },
            format="multipart",
        )

        assert respuesta.status_code == 201
        destinatarios = set(Notificacion.objects.values_list("destinatario_id", flat=True))
        assert admin.id in destinatarios
        assert vigilante.id in destinatarios
        assert residente_ajeno.id in destinatarios
        assert reportante.id not in destinatarios

    def test_incidente_prioridad_media_solo_notifica_vigilantes_y_administrador(self):
        admin = crear_usuario(
            "admin-noti-media@test.com",
            rol=Usuario.Rol.ADMINISTRADOR,
            password="Admin2026*",
            is_staff=True,
        )
        vigilante = crear_usuario(
            "vigilante-noti-media@test.com",
            rol=Usuario.Rol.VIGILANTE,
            nombre="Luis",
            apellido="Martinez",
        )
        reportante = crear_usuario("residente-reportante-media@test.com")
        residente_ajeno = crear_usuario(
            "residente-ajeno-media@test.com",
            unidad_residencial="Apto 505 Torre E",
        )
        cliente = cliente_autenticado(reportante)

        respuesta = cliente.post(
            "/api/incidentes/",
            {
                "titulo": "Ruido nocturno",
                "descripcion": "Reporte de convivencia sin riesgo inmediato.",
                "categoria": Incidente.Categoria.CONVIVENCIA,
            },
            format="multipart",
        )

        assert respuesta.status_code == 201
        destinatarios = set(Notificacion.objects.values_list("destinatario_id", flat=True))
        assert admin.id in destinatarios
        assert vigilante.id in destinatarios
        assert residente_ajeno.id not in destinatarios
        assert reportante.id not in destinatarios


class TestAsistente:
    def test_chat_asistente_responde_dentro_del_dominio(self):
        residente = crear_usuario("residente-chat-ia@test.com")
        cliente = cliente_autenticado(residente)

        with (
            patch("asistente.views._gemini_configurada", return_value=True),
            patch(
                "asistente.views._llamar_gemini",
                return_value=(
                    "Las areas comunes de Remansos del Norte funcionan de "
                    "6:00 a. m. a 10:00 p. m."
                ),
            ),
        ):
            respuesta = cliente.post(
                "/api/asistente/chat/",
                {
                    "mensaje": "Cuáles son los horarios de las áreas comunes?",
                    "historial": [],
                },
                format="json",
            )

        assert respuesta.status_code == 200
        assert respuesta.data["respuesta"].strip()
        assert respuesta.data["modo"] == "ia"
        assert respuesta.data["proveedor"] == "gemini"
        assert respuesta.data["modelo_usado"]
