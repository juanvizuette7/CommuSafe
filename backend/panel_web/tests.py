"""Pruebas del panel web administrativo."""

from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse, QueryDict
from django.test import RequestFactory, SimpleTestCase, TestCase

from incidentes.models import Incidente
from panel_web.templatetags.panel_tags import querystring
from panel_web.views import (
    _es_usuario_panel,
    _opciones_estado_disponibles,
    dashboard,
    incidente_detalle,
    incidentes_lista,
    inicio,
    login_view,
    logout_view,
    usuario_toggle_activo,
    usuarios_lista,
)


Usuario = get_user_model()


class PanelHelpersTests(SimpleTestCase):
    """Pruebas unitarias de helpers del panel web."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_querystring_preserva_filtros_y_limpia_page(self):
        request = self.factory.get("/incidentes/", data={"q": "ruido", "page": "3"})

        resultado = querystring({"request": request}, estado="EN_PROCESO")

        self.assertIn("q=ruido", resultado)
        self.assertIn("estado=EN_PROCESO", resultado)
        self.assertNotIn("page=", resultado)

    def test_querystring_elimina_parametro_si_valor_vacio(self):
        request = self.factory.get("/incidentes/")
        request.GET = QueryDict("estado=RESUELTO&q=prueba")

        resultado = querystring({"request": request}, estado="")

        self.assertIn("q=prueba", resultado)
        self.assertNotIn("estado=", resultado)

    def test_opciones_estado_disponibles_por_rol(self):
        usuario_admin = SimpleNamespace(es_administrador=True)
        usuario_vigilante = SimpleNamespace(es_administrador=False)

        incidente_resuelto = SimpleNamespace(estado=Incidente.Estado.RESUELTO)
        incidente_registrado = SimpleNamespace(estado=Incidente.Estado.REGISTRADO)
        incidente_en_proceso = SimpleNamespace(estado=Incidente.Estado.EN_PROCESO)

        self.assertEqual(_opciones_estado_disponibles(usuario_admin, incidente_resuelto), [Incidente.Estado.CERRADO])
        self.assertEqual(_opciones_estado_disponibles(usuario_vigilante, incidente_resuelto), [])
        self.assertEqual(
            _opciones_estado_disponibles(usuario_vigilante, incidente_registrado), [Incidente.Estado.EN_PROCESO]
        )
        self.assertEqual(
            _opciones_estado_disponibles(usuario_vigilante, incidente_en_proceso), [Incidente.Estado.RESUELTO]
        )


class PanelWebViewsTests(TestCase):
    """Pruebas principales del panel web."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = Usuario.objects.create_user(
            email="admin-panel@test.com",
            password="Admin2026*",
            nombre="Carlos",
            apellido="Admin",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            unidad_residencial="Oficina",
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante-panel@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
            unidad_residencial="Porteria",
        )
        self.residente = Usuario.objects.create_user(
            email="residente-panel@test.com",
            password="Commu2026*",
            nombre="Maria",
            apellido="Lopez",
            unidad_residencial="Apto 101 Torre A",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.incidente = Incidente.objects.create(
            titulo="Prueba panel",
            descripcion="Incidente para probar el panel web.",
            categoria=Incidente.Categoria.SEGURIDAD,
            reportado_por=self.residente,
        )

    def _request(self, method, path, *, user=None, data=None):
        maker = getattr(self.factory, method.lower())
        request = maker(path, data=data or {})
        request.user = user or AnonymousUser()

        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        return request

    def test_es_usuario_panel_helper(self):
        self.assertTrue(_es_usuario_panel(self.admin))
        self.assertFalse(_es_usuario_panel(self.residente))

    def test_login_get_usuario_panel_redirige_dashboard(self):
        request = self._request("get", "/login/", user=self.admin)

        response = login_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")

    def test_login_get_residente_muestra_form(self):
        request = self._request("get", "/login/", user=self.residente)

        with patch("panel_web.views.render", return_value=HttpResponse("ok")) as render_mock:
            response = login_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render_mock.call_args[0][1], "panel/login.html")

    def test_login_post_invalido(self):
        request = self._request(
            "post",
            "/login/",
            data={"email": self.admin.email, "password": "incorrecta"},
        )

        with patch("panel_web.views.render", return_value=HttpResponse("ok")):
            response = login_view(request)

        self.assertEqual(response.status_code, 200)

    def test_login_post_residente_bloqueado(self):
        request = self._request(
            "post",
            "/login/",
            data={"email": self.residente.email, "password": "Commu2026*"},
        )

        with patch("panel_web.views.render", return_value=HttpResponse("ok")):
            response = login_view(request)

        self.assertEqual(response.status_code, 200)

    def test_login_post_admin_ok(self):
        request = self._request(
            "post",
            "/login/",
            data={"email": self.admin.email, "password": "Admin2026*"},
        )

        response = login_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")

    def test_inicio_redireccion(self):
        anonimo = self._request("get", "/", user=AnonymousUser())
        response_anon = inicio(anonimo)
        self.assertEqual(response_anon.url, "/login/")

        autenticado = self._request("get", "/", user=self.admin)
        response_auth = inicio(autenticado)
        self.assertEqual(response_auth.url, "/dashboard/")

    def test_logout(self):
        request = self._request("post", "/logout/", user=self.admin)

        response = logout_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_dashboard_requiere_login(self):
        request = self._request("get", "/dashboard/", user=AnonymousUser())

        response = dashboard(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_dashboard_residente_bloqueado(self):
        request = self._request("get", "/dashboard/", user=self.residente)

        response = dashboard(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_dashboard_renderiza_contexto(self):
        request = self._request("get", "/dashboard/", user=self.admin)

        with patch("panel_web.views.render", return_value=HttpResponse("ok")) as render_mock:
            response = dashboard(request)

        self.assertEqual(response.status_code, 200)
        contexto = render_mock.call_args[0][2]
        self.assertIn("metricas", contexto)
        self.assertIn("incidentes_recientes", contexto)
        self.assertIn("grafica_incidentes_tipo", contexto)
        self.assertIn("total_incidentes", contexto)
        self.assertEqual(len(contexto["grafica_incidentes_tipo"]), len(Incidente.Categoria.choices))
        self.assertIn("grafica_incidentes_estado", contexto)
        self.assertEqual(len(contexto["grafica_incidentes_estado"]), len(Incidente.Estado.choices))

    def test_incidentes_lista_filtros(self):
        Incidente.objects.create(
            titulo="Fuga de agua",
            descripcion="Incidente de infraestructura.",
            categoria=Incidente.Categoria.INFRAESTRUCTURA,
            estado=Incidente.Estado.EN_PROCESO,
            reportado_por=self.residente,
        )

        request = self._request(
            "get",
            "/incidentes/",
            user=self.admin,
            data={
                "categoria": Incidente.Categoria.INFRAESTRUCTURA,
                "estado": Incidente.Estado.EN_PROCESO,
                "prioridad": Incidente.Prioridad.BAJA,
                "q": "fuga",
            },
        )

        with patch("panel_web.views.render", return_value=HttpResponse("ok")) as render_mock:
            response = incidentes_lista(request)

        self.assertEqual(response.status_code, 200)
        contexto = render_mock.call_args[0][2]
        self.assertEqual(contexto["page_obj"].paginator.count, 1)

    def test_incidente_detalle_get(self):
        request = self._request("get", f"/incidentes/{self.incidente.id}/", user=self.admin)

        with patch("panel_web.views.render", return_value=HttpResponse("ok")) as render_mock:
            response = incidente_detalle(request, self.incidente.id)

        self.assertEqual(response.status_code, 200)
        contexto = render_mock.call_args[0][2]
        self.assertEqual(contexto["incidente"].id, self.incidente.id)

    def test_incidente_detalle_post_exige_comentario(self):
        request = self._request(
            "post",
            f"/incidentes/{self.incidente.id}/",
            user=self.vigilante,
            data={"estado_nuevo": Incidente.Estado.EN_PROCESO, "comentario": ""},
        )

        response = incidente_detalle(request, self.incidente.id)

        self.assertEqual(response.status_code, 302)

    def test_incidente_detalle_post_invalido(self):
        request = self._request(
            "post",
            f"/incidentes/{self.incidente.id}/",
            user=self.vigilante,
            data={"estado_nuevo": Incidente.Estado.CERRADO, "comentario": "invalido"},
        )

        response = incidente_detalle(request, self.incidente.id)

        self.assertEqual(response.status_code, 302)

    def test_incidente_detalle_post_valido(self):
        request = self._request(
            "post",
            f"/incidentes/{self.incidente.id}/",
            user=self.vigilante,
            data={"estado_nuevo": Incidente.Estado.EN_PROCESO, "comentario": "Atendido correctamente"},
        )

        with patch("notificaciones.services.notificar_cambio_estado"):
            response = incidente_detalle(request, self.incidente.id)

        self.assertEqual(response.status_code, 302)
        self.incidente.refresh_from_db()
        self.assertEqual(self.incidente.estado, Incidente.Estado.EN_PROCESO)

    def test_incidente_detalle_maneja_error_serializer_no_lista(self):
        request = self._request(
            "post",
            f"/incidentes/{self.incidente.id}/",
            user=self.admin,
            data={"estado_nuevo": Incidente.Estado.EN_PROCESO, "comentario": "texto suficiente"},
        )

        class FakeSerializer:
            validated_data = {}
            errors = {"estado_nuevo": "Error simple"}

            def __init__(self, *args, **kwargs):
                pass

            def is_valid(self):
                return False

        with patch("panel_web.views.CambiarEstadoSerializer", FakeSerializer):
            response = incidente_detalle(request, self.incidente.id)

        self.assertEqual(response.status_code, 302)

    def test_usuarios_lista_filtra_rol(self):
        request = self._request(
            "get",
            "/usuarios/",
            user=self.admin,
            data={"rol": Usuario.Rol.VIGILANTE},
        )

        with patch("panel_web.views.render", return_value=HttpResponse("ok")) as render_mock:
            response = usuarios_lista(request)

        self.assertEqual(response.status_code, 200)
        usuarios = list(render_mock.call_args[0][2]["usuarios"])
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0].id, self.vigilante.id)

    def test_toggle_no_admin_bloqueado(self):
        request = self._request("post", f"/usuarios/{self.residente.id}/toggle-activo/", user=self.vigilante)

        response = usuario_toggle_activo(request, self.residente.id)

        self.assertEqual(response.status_code, 302)
        self.residente.refresh_from_db()
        self.assertTrue(self.residente.activo)

    def test_toggle_admin_no_puede_autodesactivarse(self):
        request = self._request("post", f"/usuarios/{self.admin.id}/toggle-activo/", user=self.admin)

        response = usuario_toggle_activo(request, self.admin.id)

        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_toggle_admin_exitoso_sin_referer(self):
        request = self._request("post", f"/usuarios/{self.residente.id}/toggle-activo/", user=self.admin)

        response = usuario_toggle_activo(request, self.residente.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/usuarios/")
        self.residente.refresh_from_db()
        self.assertFalse(self.residente.activo)

    def test_toggle_admin_exitoso_con_referer(self):
        request = self._request("post", f"/usuarios/{self.residente.id}/toggle-activo/", user=self.admin)
        request.META["HTTP_REFERER"] = "/usuarios/?rol=RESIDENTE"

        response = usuario_toggle_activo(request, self.residente.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/usuarios/?rol=RESIDENTE")
