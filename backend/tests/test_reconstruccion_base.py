from io import StringIO

import pytest
from django.core.management import call_command

from asistente.models import ConversacionAsistente, EntradaConocimiento, MensajeAsistente
from incidentes.models import HistorialEstado, Incidente
from notificaciones.models import AvisoProgramado, Notificacion
from usuarios.models import Usuario


pytestmark = pytest.mark.django_db


def ejecutar_reconstruccion():
    salida = StringIO()
    call_command("reconstruir_base_segura", stdout=salida)
    return salida.getvalue()


def conteos():
    return {
        "usuarios": Usuario.objects.count(),
        "incidentes": Incidente.objects.count(),
        "historiales": HistorialEstado.objects.count(),
        "avisos": AvisoProgramado.objects.count(),
        "notificaciones": Notificacion.objects.count(),
        "conversaciones": ConversacionAsistente.objects.count(),
        "mensajes": MensajeAsistente.objects.count(),
        "conocimiento": EntradaConocimiento.objects.count(),
    }


def test_reconstruccion_crea_un_entorno_funcional_y_es_idempotente():
    primera_salida = ejecutar_reconstruccion()
    primera_ejecucion = conteos()
    segunda_salida = ejecutar_reconstruccion()
    segunda_ejecucion = conteos()

    assert primera_ejecucion == segunda_ejecucion
    assert primera_ejecucion["usuarios"] >= 8
    assert primera_ejecucion["incidentes"] >= 4
    assert primera_ejecucion["historiales"] >= 3
    assert primera_ejecucion["avisos"] >= 1
    assert primera_ejecucion["notificaciones"] >= 1
    assert primera_ejecucion["conversaciones"] >= 1
    assert primera_ejecucion["mensajes"] >= 2
    assert primera_ejecucion["conocimiento"] >= 100
    assert "Reconstrucción idempotente completada." in primera_salida
    assert "Usuarios creados: 0" in segunda_salida


def test_reconstruccion_no_sobrescribe_usuario_existente():
    usuario = Usuario.objects.create_user(
        email="residente1@remansos.com",
        password="ClavePropia2026*",
        nombre="Nombre",
        apellido="Conservado",
        rol=Usuario.Rol.RESIDENTE,
        unidad_residencial="Unidad existente",
    )

    ejecutar_reconstruccion()
    usuario.refresh_from_db()

    assert usuario.nombre == "Nombre"
    assert usuario.apellido == "Conservado"
    assert usuario.unidad_residencial == "Unidad existente"
    assert usuario.check_password("ClavePropia2026*")
