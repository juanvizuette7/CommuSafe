"""Sincronizacion del historial y del indice de conocimiento local."""

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import EntradaConocimiento, VersionEntradaConocimiento


def _refrescar_motor():
    from .local_engine import refresh_local_engine

    refresh_local_engine(force=True)


@receiver(post_save, sender=EntradaConocimiento)
def registrar_version_conocimiento(sender, instance, **kwargs):
    """Conserva un snapshot inmutable por cada version publicada o editada."""

    VersionEntradaConocimiento.objects.get_or_create(
        entrada=instance,
        version=instance.version,
        defaults={
            "datos": instance.snapshot(),
            "cambiado_por": instance.actualizado_por or instance.creado_por,
        },
    )
    transaction.on_commit(_refrescar_motor)


@receiver(post_delete, sender=EntradaConocimiento)
def retirar_entrada_del_motor(sender, instance, **kwargs):
    transaction.on_commit(_refrescar_motor)
