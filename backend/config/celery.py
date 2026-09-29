"""Aplicacao Celery do projeto (worker + beat da coleta de noticias).

    celery -A config worker -l info            # Windows: acrescente --pool=solo
    celery -A config beat -l info
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("pauta")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
