"""Crea o actualiza el administrador inicial de produccion."""

from decouple import config
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un administrador inicial usando variables PROD_ADMIN_* si estan configuradas."

    def handle(self, *args, **options):
        email = config("PROD_ADMIN_EMAIL", default="").strip().lower()
        password = config("PROD_ADMIN_PASSWORD", default="")
        nombre = config("PROD_ADMIN_NOMBRE", default="Administrador").strip() or "Administrador"
        apellido = config("PROD_ADMIN_APELLIDO", default="CommuSafe").strip() or "CommuSafe"
        telefono = config("PROD_ADMIN_TELEFONO", default="").strip()

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "PROD_ADMIN_EMAIL o PROD_ADMIN_PASSWORD no estan configuradas. "
                    "Se omite la creacion del administrador inicial."
                )
            )
            return

        Usuario = get_user_model()
        usuario, creado = Usuario.objects.get_or_create(
            email=email,
            defaults={
                "nombre": nombre,
                "apellido": apellido,
                "rol": Usuario.Rol.ADMINISTRADOR,
                "telefono": telefono,
                "activo": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        usuario.nombre = nombre
        usuario.apellido = apellido
        usuario.rol = Usuario.Rol.ADMINISTRADOR
        usuario.telefono = telefono
        usuario.activo = True
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.set_password(password)
        usuario.full_clean()
        usuario.save()

        accion = "creado" if creado else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Administrador de produccion {accion}: {email}"))
