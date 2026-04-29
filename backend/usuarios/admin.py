"""Configuración del admin para usuarios."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import PasswordResetToken, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin del modelo de usuario personalizado."""

    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario
    ordering = ("-fecha_registro",)
    list_display = (
        "email",
        "nombre_completo_admin",
        "rol",
        "unidad_residencial",
        "activo",
        "fecha_registro",
    )
    list_filter = ("rol", "activo", "is_staff", "is_superuser")
    search_fields = ("email", "nombre", "apellido")
    readonly_fields = ("fecha_registro", "last_login")
    fieldsets = (
        ("Acceso", {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("nombre", "apellido", "unidad_residencial", "telefono", "foto_perfil")}),
        ("Permisos", {"fields": ("rol", "activo", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "fecha_registro")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nombre",
                    "apellido",
                    "unidad_residencial",
                    "rol",
                    "telefono",
                    "foto_perfil",
                    "activo",
                    "is_staff",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    @admin.display(description="Nombre completo")
    def nombre_completo_admin(self, obj):
        return obj.nombre_completo


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin de auditoria para recuperaciones de contrasena."""

    list_display = ("usuario", "creado", "expira", "usado", "esta_vigente")
    list_filter = ("usado", "creado", "expira")
    search_fields = ("usuario__email", "usuario__nombre", "usuario__apellido", "token")
    readonly_fields = ("id", "usuario", "token", "creado", "expira", "usado")

    @admin.display(boolean=True, description="Vigente")
    def esta_vigente(self, obj):
        return obj.esta_vigente
