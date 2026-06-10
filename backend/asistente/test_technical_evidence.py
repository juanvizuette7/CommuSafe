"""Pruebas del generador reproducible de evidencia tecnica."""

from collections import Counter

from django.test import TestCase

from .technical_evidence import _classification_metrics, _run_concurrency


class TechnicalEvidenceTests(TestCase):
    def test_metricas_clasificacion_calculan_precision_recall_y_f1(self):
        confusion = {
            "intencion_a": Counter({"intencion_a": 4, "intencion_b": 1}),
            "intencion_b": Counter({"intencion_b": 3, "intencion_a": 2}),
        }

        metrics = _classification_metrics(confusion, {"intencion_a", "intencion_b"})

        self.assertEqual(metrics["precision_micro"], 0.7)
        self.assertEqual(metrics["recall_micro"], 0.7)
        self.assertEqual(metrics["por_intencion"]["intencion_a"]["soporte"], 5)
        self.assertEqual(metrics["por_intencion"]["intencion_b"]["falsos_positivos"], 1)

    def test_concurrencia_no_mezcla_resultados_ni_usa_ia_externa(self):
        result = _run_concurrency(total=40, workers=8)

        self.assertEqual(result["exitosas"], 40)
        self.assertEqual(result["errores"], [])
        self.assertEqual(result["contaminaciones_cache"], 0)
        self.assertTrue(result["aislamiento_aprobado"])
        self.assertFalse(result["ia_externa_usada"])
