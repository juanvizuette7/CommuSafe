"""Formularios administrativos para el modelo Usuario."""

from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import get_user_model


Usuario = get_user_model()


class UsuarioCreationForm(forms.ModelForm):
    """Formulario de creación para el admin de Django."""

    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = (
            "email",
            "nombre",
            "apellido",
            "unidad_residencial",
            "rol",
            "telefono",
            "foto_perfil",
            "activo",
            "is_staff",
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario


class UsuarioChangeForm(forms.ModelForm):
    """Formulario de edición para el admin de Django."""

    password = ReadOnlyPasswordHashField(label="Contraseña")

    class Meta:
        model = Usuario
        fields = (
            "email",
            "nombre",
            "apellido",
            "unidad_residencial",
            "rol",
            "telefono",
            "foto_perfil",
            "password",
            "activo",
            "is_staff",
            "is_superuser",
        )

    def clean_password(self):
        return self.initial["password"]
