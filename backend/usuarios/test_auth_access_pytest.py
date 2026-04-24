"""Pruebas del Incremento 1: nucleo del sistema y autenticacion."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


Usuario = get_user_model()


class Incremento1AutenticacionTests(APITestCase):
    """Cubre registro administrativo, login, logout y permisos base por rol."""

    password = "Commu2026*"

    def setUp(self):
        self.admin = self.crear_usuario(
            "admin-inc1@test.com",
            Usuario.Rol.ADMINISTRADOR,
            nombre="Admin",
            apellido="Principal",
        )
        self.vigilante = self.crear_usuario(
            "vigilante-inc1@test.com",
            Usuario.Rol.VIGILANTE,
            nombre="Victor",
            apellido="Guardia",
        )
        self.residente = self.crear_usuario(
            "residente-inc1@test.com",
            Usuario.Rol.RESIDENTE,
            nombre="Rosa",
            apellido="Residente",
            unidad_residencial="Torre A 101",
        )

    def crear_usuario(self, email, rol, password=None, **extra):
        datos = {
            "nombre": extra.pop("nombre", "Usuario"),
            "apellido": extra.pop("apellido", rol.title()),
            "rol": rol,
            "unidad_residencial": extra.pop("unidad_residencial", "Torre A 101"),
        }
        if rol == Usuario.Rol.ADMINISTRADOR:
            datos["is_staff"] = True
            datos["unidad_residencial"] = extra.pop("unidad_residencial", "Oficina")
        elif rol == Usuario.Rol.VIGILANTE:
            datos["unidad_residencial"] = extra.pop("unidad_residencial", "Porteria")
        datos.update(extra)
        return Usuario.objects.create_user(email=email, password=password or self.password, **datos)

    def datos_registro(self, email, rol, unidad_residencial):
        return {
            "email": email,
            "password": self.password,
            "nombre": "Nuevo",
            "apellido": rol.title(),
            "rol": rol,
            "unidad_residencial": unidad_residencial,
        }

    def test_login_devuelve_tokens_y_datos_del_usuario(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {"email": self.admin.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["usuario"]["email"], self.admin.email)
        self.assertEqual(response.data["usuario"]["rol"], Usuario.Rol.ADMINISTRADOR)

    def test_login_rechaza_credenciales_invalidas(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {"email": self.residente.email, "password": "ClaveIncorrecta2026*"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_valida_campos_obligatorios(self):
        sin_email = self.client.post(
            reverse("usuarios:login"),
            {"password": self.password},
            format="json",
        )
        sin_password = self.client.post(
            reverse("usuarios:login"),
            {"email": self.admin.email},
            format="json",
        )

        self.assertEqual(sin_email.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sin_password.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", sin_email.data)
        self.assertIn("password", sin_password.data)

    def test_refresh_renueva_access_token(self):
        refresh = RefreshToken.for_user(self.vigilante)

        response = self.client.post(
            reverse("usuarios:refresh"),
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_panel_cierra_sesion_cuando_existe_ruta(self):
        login_ok = self.client.login(email=self.admin.email, password=self.password)
        self.assertTrue(login_ok)
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.post(reverse("panel_web:logout"))

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, reverse("panel_web:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_registra_usuarios_con_roles_permitidos(self):
        self.client.force_authenticate(self.admin)
        casos = [
            (Usuario.Rol.RESIDENTE, "Torre B 203"),
            (Usuario.Rol.VIGILANTE, "Porteria"),
            (Usuario.Rol.ADMINISTRADOR, "Oficina"),
        ]

        for rol, unidad in casos:
            with self.subTest(rol=rol):
                email = f"{rol.lower()}-registro-inc1@test.com"
                response = self.client.post(
                    reverse("usuarios:usuario-list"),
                    self.datos_registro(email, rol, unidad),
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data["email"], email)
                self.assertEqual(response.data["rol"], rol)

                usuario = Usuario.objects.get(email=email)
                self.assertTrue(usuario.check_password(self.password))
                self.assertEqual(usuario.rol, rol)
                self.assertEqual(usuario.is_staff, rol == Usuario.Rol.ADMINISTRADOR)

    def test_usuarios_registrados_por_rol_pueden_iniciar_sesion(self):
        self.client.force_authenticate(self.admin)
        roles = [Usuario.Rol.RESIDENTE, Usuario.Rol.VIGILANTE, Usuario.Rol.ADMINISTRADOR]

        for rol in roles:
            with self.subTest(rol=rol):
                email = f"{rol.lower()}-login-inc1@test.com"
                registro = self.client.post(
                    reverse("usuarios:usuario-list"),
                    self.datos_registro(email, rol, "Torre C 301"),
                    format="json",
                )
                self.assertEqual(registro.status_code, status.HTTP_201_CREATED)

                self.client.force_authenticate(user=None)
                login = self.client.post(
                    reverse("usuarios:login"),
                    {"email": email, "password": self.password},
                    format="json",
                )

                self.assertEqual(login.status_code, status.HTTP_200_OK)
                self.assertEqual(login.data["usuario"]["rol"], rol)
                self.client.force_authenticate(self.admin)

    def test_registro_valida_campos_obligatorios(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("usuarios:usuario-list"),
            {
                "email": "",
                "password": "",
                "nombre": "",
                "apellido": "",
                "rol": Usuario.Rol.RESIDENTE,
                "unidad_residencial": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)
        self.assertIn("nombre", response.data)
        self.assertIn("apellido", response.data)

        sin_unidad = self.client.post(
            reverse("usuarios:usuario-list"),
            {
                "email": "residente-sin-unidad-inc1@test.com",
                "password": self.password,
                "nombre": "Residente",
                "apellido": "SinUnidad",
                "rol": Usuario.Rol.RESIDENTE,
                "unidad_residencial": "",
            },
            format="json",
        )
        self.assertEqual(sin_unidad.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unidad_residencial", sin_unidad.data)

    def test_registro_rechaza_email_duplicado(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("usuarios:usuario-list"),
            self.datos_registro(self.residente.email, Usuario.Rol.RESIDENTE, "Torre B 204"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_residente_no_accede_a_rutas_de_administrador(self):
        self.client.force_authenticate(self.residente)

        listar = self.client.get(reverse("usuarios:usuario-list"))
        crear = self.client.post(
            reverse("usuarios:usuario-list"),
            self.datos_registro("residente-sin-permiso@test.com", Usuario.Rol.RESIDENTE, "Torre D 401"),
            format="json",
        )

        self.assertEqual(listar.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(crear.status_code, status.HTTP_403_FORBIDDEN)

    def test_vigilante_no_accede_a_rutas_administrativas_no_autorizadas(self):
        self.client.force_authenticate(self.vigilante)

        listar = self.client.get(reverse("usuarios:usuario-list"))
        cambiar_rol = self.client.post(
            reverse("usuarios:usuario-cambiar-rol", args=[self.residente.id]),
            {"rol": Usuario.Rol.ADMINISTRADOR},
            format="json",
        )

        self.assertEqual(listar.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(cambiar_rol.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_accede_a_rutas_protegidas_de_administracion(self):
        self.client.force_authenticate(self.admin)

        listar = self.client.get(reverse("usuarios:usuario-list"))
        cambiar_rol = self.client.post(
            reverse("usuarios:usuario-cambiar-rol", args=[self.vigilante.id]),
            {"rol": Usuario.Rol.ADMINISTRADOR},
            format="json",
        )

        self.assertEqual(listar.status_code, status.HTTP_200_OK)
        self.assertEqual(cambiar_rol.status_code, status.HTTP_200_OK)
        self.vigilante.refresh_from_db()
        self.assertEqual(self.vigilante.rol, Usuario.Rol.ADMINISTRADOR)
        self.assertTrue(self.vigilante.is_staff)

    def test_perfil_requiere_autenticacion_y_permite_usuario_autenticado(self):
        anonimo = self.client.get(reverse("usuarios:perfil"))
        self.client.force_authenticate(self.residente)
        autenticado = self.client.get(reverse("usuarios:perfil"))

        self.assertEqual(anonimo.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(autenticado.status_code, status.HTTP_200_OK)
        self.assertEqual(autenticado.data["email"], self.residente.email)
        self.assertEqual(autenticado.data["rol"], Usuario.Rol.RESIDENTE)
