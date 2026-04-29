"""Formularios del panel web para la gestion administrativa de usuarios."""

from django import forms
from django.core.validators import MinLengthValidator

from usuarios.models import Usuario


INPUT_CLASS = (
    "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm "
    "font-medium text-slate-800 outline-none transition placeholder:text-slate-400 "
    "focus:border-accent focus:bg-white focus:ring-4 focus:ring-accent/10"
)
SELECT_CLASS = (
    "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm "
    "font-semibold text-slate-800 outline-none transition focus:border-accent "
    "focus:bg-white focus:ring-4 focus:ring-accent/10"
)
CHECKBOX_CLASS = "h-5 w-5 rounded border-slate-300 text-primary focus:ring-accent"


class _UsuarioPanelFormMixin:
    """Utilidades comunes para formularios de usuario del panel."""

    def _aplicar_estilos(self):
        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs.update({"class": CHECKBOX_CLASS})
                continue
            if isinstance(campo.widget, forms.Select):
                campo.widget.attrs.update({"class": SELECT_CLASS})
                continue
            campo.widget.attrs.update({"class": INPUT_CLASS})

            if nombre == "email":
                campo.widget.attrs.update({"placeholder": "correo@ejemplo.com"})
            elif nombre == "nombre":
                campo.widget.attrs.update({"placeholder": "Nombre"})
            elif nombre == "apellido":
                campo.widget.attrs.update({"placeholder": "Apellido"})
            elif nombre == "unidad_residencial":
                campo.widget.attrs.update({"placeholder": "Apto 301 Torre A"})
            elif nombre == "telefono":
                campo.widget.attrs.update({"placeholder": "3001234567"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        queryset = Usuario.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")
        unidad = (cleaned_data.get("unidad_residencial") or "").strip()
        if rol == Usuario.Rol.RESIDENTE and not unidad:
            self.add_error(
                "unidad_residencial",
                "La unidad residencial es obligatoria para residentes.",
            )
        return cleaned_data


class UsuarioCreacionForm(_UsuarioPanelFormMixin, forms.ModelForm):
    """Formulario para crear usuarios desde el panel web."""

    password1 = forms.CharField(
        label="Contraseña",
        validators=[MinLengthValidator(8, "La contraseña debe tener mínimo 8 caracteres.")],
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Mínimo 8 caracteres",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        validators=[MinLengthValidator(8, "La contraseña debe tener mínimo 8 caracteres.")],
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Repite la contraseña",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = Usuario
        fields = [
            "email",
            "nombre",
            "apellido",
            "rol",
            "unidad_residencial",
            "telefono",
        ]
        labels = {
            "email": "Correo electrónico",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "rol": "Rol",
            "unidad_residencial": "Unidad residencial",
            "telefono": "Teléfono",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

    def save(self, commit=True):
        datos = self.cleaned_data.copy()
        password = datos.pop("password1")
        datos.pop("password2", None)
        usuario = Usuario(**datos)
        usuario.activo = True
        usuario.is_staff = usuario.rol == Usuario.Rol.ADMINISTRADOR
        usuario.set_password(password)
        usuario.full_clean()
        if commit:
            usuario.save()
        return usuario


class UsuarioEdicionForm(_UsuarioPanelFormMixin, forms.ModelForm):
    """Formulario para editar usuarios desde el panel web."""

    class Meta:
        model = Usuario
        fields = [
            "email",
            "nombre",
            "apellido",
            "rol",
            "unidad_residencial",
            "telefono",
            "activo",
        ]
        labels = {
            "email": "Correo electrónico",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "rol": "Rol",
            "unidad_residencial": "Unidad residencial",
            "telefono": "Teléfono",
            "activo": "Cuenta activa",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_staff = usuario.rol == Usuario.Rol.ADMINISTRADOR or usuario.is_superuser
        usuario.full_clean()
        if commit:
            usuario.save()
        return usuario


class PasswordResetSolicitudForm(forms.Form):
    """Formulario publico para solicitar enlace de recuperacion."""

    email = forms.EmailField(
        label="Correo electronico",
        widget=forms.EmailInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "correo@ejemplo.com",
                "autocomplete": "email",
            }
        ),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class PasswordResetConfirmacionForm(forms.Form):
    """Formulario publico para definir una contrasena nueva."""

    password = forms.CharField(
        label="Nueva contrasena",
        validators=[MinLengthValidator(8, "La contrasena debe tener minimo 8 caracteres.")],
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Minimo 8 caracteres",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmar contrasena",
        validators=[MinLengthValidator(8, "La contrasena debe tener minimo 8 caracteres.")],
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "Repite la contrasena",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            self.add_error("password2", "Las contrasenas no coinciden.")
        return cleaned_data
