"""Pruebas del recorrido academico reproducible de CommuBot."""

from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from .local_engine import resolve_local_answer
from .management.commands.demostrar_asistente_hibrido import DEMO_CASES


class DemoCasesTests(SimpleTestCase):
    def test_casos_de_demo_conservan_decisiones_locales_esperadas(self):
        for caso in DEMO_CASES:
            with self.subTest(caso=caso.codigo):
                resultado = resolve_local_answer(caso.mensaje, "RESIDENTE")
                self.assertEqual(resultado["action"], caso.accion_local_esperada)


@override_settings(LLM_BACKUP_ENABLED=False)
class DemoCommandTests(TestCase):
    def test_recorrido_sin_gemini_no_invoca_proveedor_externo(self):
        salida = StringIO()

        call_command(
            "demostrar_asistente_hibrido",
            solicitudes=12,
            workers=3,
            stdout=salida,
        )

        texto = salida.getvalue()
        self.assertIn("ASISTENTE LISTO PARA LA DEMOSTRACION ACADEMICA", texto)
        self.assertIn("Gemini preparado, pero no invocado", texto)
