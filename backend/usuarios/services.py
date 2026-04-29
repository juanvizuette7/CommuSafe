"""Servicios de autenticacion y recuperacion de cuentas."""

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import PasswordResetToken


class PasswordResetError(ValueError):
    """Error controlado para respuestas de recuperacion de contrasena."""


def _resolver_base_url(request):
    host = request.get_host()
    host_local = host.startswith(("localhost", "127.0.0.1", "10.0.2.2"))
    scheme = request.scheme if settings.DEBUG and host_local else "https"
    return f"{scheme}://{host}"


def crear_y_enviar_token_reset(usuario, request):
    """Crea un token nuevo e intenta enviarlo por correo al usuario."""

    PasswordResetToken.objects.filter(
        usuario=usuario,
        usado=False,
        expira__gt=timezone.now(),
    ).update(usado=True)

    reset = PasswordResetToken.objects.create(usuario=usuario)
    enlace = f"{_resolver_base_url(request)}{reverse('panel_web:reset_confirmar', kwargs={'token': reset.token})}"
    asunto = "Recuperacion de contrasena - CommuSafe"
    cuerpo = (
        f"Hola {usuario.nombre},\n\n"
        "Recibimos una solicitud para restablecer tu contrasena en CommuSafe.\n"
        "Usa el siguiente enlace durante la proxima hora:\n\n"
        f"{enlace}\n\n"
        "Si no solicitaste este cambio, ignora este mensaje."
    )

    send_mail(
        subject=asunto,
        message=cuerpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        fail_silently=False,
    )
    return reset


def confirmar_reset_password(token, password):
    """Valida un token vigente y actualiza la contrasena del usuario."""

    reset = PasswordResetToken.objects.select_related("usuario").filter(token=token).first()
    if reset is None or not reset.esta_vigente:
        raise PasswordResetError("El enlace de recuperacion no es valido o ya expiro.")

    usuario = reset.usuario
    try:
        validate_password(password, user=usuario)
    except ValidationError as exc:
        raise PasswordResetError(" ".join(str(error) for error in exc.messages)) from exc

    usuario.set_password(password)
    usuario.save(update_fields=["password"])
    reset.usado = True
    reset.save(update_fields=["usado"])
    return usuario
