"""Pruebas del modulo de usuarios."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .forms import UsuarioChangeForm, UsuarioCreationForm
from .serializers import UsuarioAdminUpdateSerializer, UsuarioCreateSerializer


Usuario = get_user_model()


class UsuarioModelTests(APITestCase):
    """Pruebas basicas del modelo de usuario."""

    def test_create_user_exige_email_y_password(self):
        with self.assertRaisesMessage(ValueError, "El correo"):
            Usuario.objects.create_user(
                email="",
                password="Segura2026*",
                nombre="Sin",
                apellido="Email",
                rol=Usuario.Rol.VIGILANTE,
            )

        with self.assertRaisesMessage(ValueError, "La contrase"):
            Usuario.objects.create_user(
                email="sin-password@remansos.com",
                password="",
                nombre="Sin",
                apellido="Password",
                rol=Usuario.Rol.VIGILANTE,
            )

    def test_crea_usuario_con_email_normalizado(self):
        usuario = Usuario.objects.create_user(
            email="USUARIO@REMANSOS.COM",
            password="Segura2026*",
            nombre="Laura",
            apellido="Rios",
            rol=Usuario.Rol.VIGILANTE,
        )

        self.assertEqual(usuario.email, "usuario@remansos.com")

    def test_residente_requiere_unidad_residencial(self):
        with self.assertRaises(ValidationError):
            Usuario.objects.create_user(
                email="residente@remansos.com",
                password="Segura2026*",
                nombre="Ana",
                apellido="Perez",
                rol=Usuario.Rol.RESIDENTE,
                unidad_residencial="",
            )

    def test_create_superuser_configura_flags_obligatorios(self):
        usuario = Usuario.objects.create_superuser(
            email="root@remansos.com",
            password="Admin2026*",
            nombre="Root",
            apellido="Admin",
            unidad_residencial="Oficina",
        )

        self.assertTrue(usuario.is_superuser)
        self.assertTrue(usuario.is_staff)
        self.assertEqual(usuario.rol, Usuario.Rol.ADMINISTRADOR)

    def test_create_superuser_valida_flags_obligatorios(self):
        with self.assertRaisesMessage(ValueError, "is_staff=True"):
            Usuario.objects.create_superuser(
                email="staff-falso@remansos.com",
                password="Admin2026*",
                nombre="Root",
                apellido="Admin",
                unidad_residencial="Oficina",
                is_staff=False,
            )

        with self.assertRaisesMessage(ValueError, "is_superuser=True"):
            Usuario.objects.create_superuser(
                email="superuser-falso@remansos.com",
                password="Admin2026*",
                nombre="Root",
                apellido="Admin",
                unidad_residencial="Oficina",
                is_superuser=False,
            )

    def test_representacion_nombres_y_alias_is_active(self):
        usuario = Usuario.objects.create_user(
            email="alias@remansos.com",
            password="Segura2026*",
            nombre="Laura",
            apellido="Rios",
            rol=Usuario.Rol.VIGILANTE,
        )

        self.assertEqual(str(usuario), "Laura Rios <alias@remansos.com>")
        self.assertEqual(usuario.get_full_name(), "Laura Rios")
        self.assertEqual(usuario.get_short_name(), "Laura")

        usuario.is_active = False
        self.assertFalse(usuario.activo)


class LoginJWTTests(APITestCase):
    """Pruebas del flujo de autenticacion JWT."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="admin@remansos.com",
            password="Admin2026*",
            nombre="Carlos",
            apellido="Gonzalez",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            unidad_residencial="Oficina",
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
        self.assertEqual(response.data["usuario"]["rol"], Usuario.Rol.ADMINISTRADOR)

    def test_login_falla_si_usuario_esta_inactivo(self):
        self.usuario.activo = False
        self.usuario.save(update_fields=["activo"])

        response = self.client.post(
            reverse("usuarios:login"),
            {"email": self.usuario.email, "password": "Admin2026*"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class PerfilYFCMEndpointsTests(APITestCase):
    """Pruebas de perfil propio y actualizacion de token FCM."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="residente@remansos.com",
            password="Segura2026*",
            nombre="Laura",
            apellido="Mora",
            unidad_residencial="Apto 101",
            rol=Usuario.Rol.RESIDENTE,
        )
        self.client.force_authenticate(self.usuario)

    def test_obtener_perfil_propio(self):
        response = self.client.get(reverse("usuarios:perfil"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.usuario.email)

    def test_actualizar_perfil_propio(self):
        response = self.client.put(
            reverse("usuarios:perfil"),
            {"nombre": "Luisa", "telefono": "3001234567"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre, "Luisa")
        self.assertEqual(self.usuario.telefono, "3001234567")

    def test_residente_no_puede_quedar_sin_unidad(self):
        response = self.client.put(
            reverse("usuarios:perfil"),
            {"unidad_residencial": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unidad_residencial", response.data)

    def test_actualizar_fcm_token(self):
        response = self.client.post(
            reverse("usuarios:fcm"),
            {"fcm_token": "token-valido-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.fcm_token, "token-valido-123")

    def test_rechaza_fcm_token_vacio(self):
        response = self.client.post(
            reverse("usuarios:fcm"),
            {"fcm_token": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fcm_token", response.data)


class UsuarioViewSetTests(APITestCase):
    """Pruebas de gestion administrativa de usuarios."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin-users@test.com",
            password="Admin2026*",
            nombre="Admin",
            apellido="Principal",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            unidad_residencial="Oficina",
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante-users@test.com",
            password="Commu2026*",
            nombre="Pedro",
            apellido="Guardia",
            rol=Usuario.Rol.VIGILANTE,
            unidad_residencial="Porteria",
        )
        self.residente = Usuario.objects.create_user(
            email="residente-users@test.com",
            password="Commu2026*",
            nombre="Maria",
            apellido="Lopez",
            rol=Usuario.Rol.RESIDENTE,
            unidad_residencial="Apto 202",
        )

    def test_no_admin_no_puede_listar_usuarios(self):
        self.client.force_authenticate(self.vigilante)

        response = self.client.get(reverse("usuarios:usuario-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_desactiva_usuario_en_destroy_logico(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse("usuarios:usuario-detail", args=[self.residente.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.residente.refresh_from_db()
        self.assertFalse(self.residente.activo)

    def test_admin_puede_activar_y_desactivar_usuario(self):
        self.client.force_authenticate(self.admin)

        desactivar = self.client.post(reverse("usuarios:usuario-desactivar", args=[self.residente.id]))
        self.assertEqual(desactivar.status_code, status.HTTP_200_OK)
        self.residente.refresh_from_db()
        self.assertFalse(self.residente.activo)

        activar = self.client.post(reverse("usuarios:usuario-activar", args=[self.residente.id]))
        self.assertEqual(activar.status_code, status.HTTP_200_OK)
        self.residente.refresh_from_db()
        self.assertTrue(self.residente.activo)

    def test_cambiar_rol_actualiza_is_staff(self):
        self.client.force_authenticate(self.admin)

        subir = self.client.post(
            reverse("usuarios:usuario-cambiar-rol", args=[self.vigilante.id]),
            {"rol": Usuario.Rol.ADMINISTRADOR},
            format="json",
        )
        self.assertEqual(subir.status_code, status.HTTP_200_OK)
        self.vigilante.refresh_from_db()
        self.assertTrue(self.vigilante.is_staff)

        bajar = self.client.post(
            reverse("usuarios:usuario-cambiar-rol", args=[self.vigilante.id]),
            {"rol": Usuario.Rol.RESIDENTE},
            format="json",
        )
        self.assertEqual(bajar.status_code, status.HTTP_200_OK)
        self.vigilante.refresh_from_db()
        self.assertFalse(self.vigilante.is_staff)

    def test_admin_no_puede_crear_residente_sin_unidad(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("usuarios:usuario-list"),
            {
                "email": "nuevo@test.com",
                "password": "Segura2026*",
                "nombre": "Nuevo",
                "apellido": "Usuario",
                "rol": Usuario.Rol.RESIDENTE,
                "unidad_residencial": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unidad_residencial", response.data)


class UsuariosFormsYSerializersTests(TestCase):
    """Pruebas unitarias para formularios y serializers de usuarios."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin-serial@test.com",
            password="Admin2026*",
            nombre="Admin",
            apellido="Uno",
            rol=Usuario.Rol.ADMINISTRADOR,
            is_staff=True,
            unidad_residencial="Oficina",
        )
        self.vigilante = Usuario.objects.create_user(
            email="vigilante-serial@test.com",
            password="Commu2026*",
            nombre="Vigi",
            apellido="Lante",
            rol=Usuario.Rol.VIGILANTE,
            unidad_residencial="Porteria",
        )

    def test_usuario_creation_form_valida_password_y_save(self):
        form_invalido = UsuarioCreationForm(
            data={
                "email": "form@test.com",
                "nombre": "Form",
                "apellido": "Test",
                "rol": Usuario.Rol.VIGILANTE,
                "activo": True,
                "is_staff": False,
                "password1": "Clave2026*",
                "password2": "Distinta2026*",
            }
        )
        self.assertFalse(form_invalido.is_valid())
        self.assertIn("password2", form_invalido.errors)

        form_valido = UsuarioCreationForm(
            data={
                "email": "form-ok@test.com",
                "nombre": "Form",
                "apellido": "Ok",
                "rol": Usuario.Rol.VIGILANTE,
                "activo": True,
                "is_staff": False,
                "password1": "Clave2026*",
                "password2": "Clave2026*",
            }
        )
        self.assertTrue(form_valido.is_valid(), form_valido.errors)
        usuario = form_valido.save(commit=False)
        self.assertTrue(usuario._state.adding)
        self.assertFalse(Usuario.objects.filter(email="form-ok@test.com").exists())
        self.assertTrue(usuario.check_password("Clave2026*"))
        usuario.save()
        self.assertIsNotNone(usuario.pk)

    def test_usuario_change_form_clean_password(self):
        form = UsuarioChangeForm(instance=self.admin, initial={"password": "hash-simulado"})
        self.assertEqual(form.clean_password(), "hash-simulado")

    def test_usuario_create_serializer_casos_principales(self):
        duplicado = UsuarioCreateSerializer(
            data={
                "email": self.admin.email,
                "nombre": "Otro",
                "apellido": "Admin",
                "rol": Usuario.Rol.VIGILANTE,
                "password": "Clave2026*",
            }
        )
        self.assertFalse(duplicado.is_valid())
        self.assertIn("email", duplicado.errors)

        sin_unidad = UsuarioCreateSerializer(
            data={
                "email": "residente-sin-unidad@test.com",
                "nombre": "Resi",
                "apellido": "Sin",
                "rol": Usuario.Rol.RESIDENTE,
                "unidad_residencial": "",
                "password": "Clave2026*",
            }
        )
        self.assertFalse(sin_unidad.is_valid())
        self.assertIn("unidad_residencial", sin_unidad.errors)

        admin_serializer = UsuarioCreateSerializer(
            data={
                "email": "nuevo-admin@test.com",
                "nombre": "Nuevo",
                "apellido": "Admin",
                "rol": Usuario.Rol.ADMINISTRADOR,
                "unidad_residencial": "Oficina",
                "password": "Clave2026*",
            }
        )
        self.assertTrue(admin_serializer.is_valid(), admin_serializer.errors)
        nuevo_admin = admin_serializer.save()
        self.assertTrue(nuevo_admin.is_staff)

    def test_usuario_admin_update_serializer_cubre_validaciones_y_update(self):
        residente = Usuario.objects.create_user(
            email="residente-serial@test.com",
            password="Resi2026*",
            nombre="Resi",
            apellido="Prueba",
            rol=Usuario.Rol.RESIDENTE,
            unidad_residencial="Apto 101",
        )

        duplicado_email = UsuarioAdminUpdateSerializer(
            instance=self.vigilante,
            data={"email": self.admin.email},
            partial=True,
        )
        self.assertFalse(duplicado_email.is_valid())
        self.assertIn("email", duplicado_email.errors)

        sin_unidad = UsuarioAdminUpdateSerializer(
            instance=residente,
            data={"unidad_residencial": ""},
            partial=True,
        )
        self.assertFalse(sin_unidad.is_valid())
        self.assertIn("unidad_residencial", sin_unidad.errors)

        serializer = UsuarioAdminUpdateSerializer(
            instance=self.vigilante,
            data={
                "email": "vigilante-actualizado@test.com",
                "rol": Usuario.Rol.ADMINISTRADOR,
                "password": "NuevaClave2026*",
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        actualizado = serializer.save()
        self.assertTrue(actualizado.check_password("NuevaClave2026*"))
        self.assertTrue(actualizado.is_staff)
