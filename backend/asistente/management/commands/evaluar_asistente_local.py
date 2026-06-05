"""Evalua el motor local hibrido del asistente."""

import json

from django.core.management.base import BaseCommand

from asistente.evaluation import evaluate_all


class Command(BaseCommand):
    help = "Evalua el motor local de CommuBot con splits train/validation/test."

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(evaluate_all(), ensure_ascii=False, indent=2))
