"""Aplicacao Celery do projeto (worker + beat da coleta de noticias).

    celery -A config worker -l info            # Windows: acrescente --pool=solo
    celery -A config beat -l info

O beat dispara `apps.coleta.tasks.coletar_noticias` (que executa
`manage.py coletar_noticias`) a cada COLETA_INTERVALO_MINUTOS (40 por padrao).
"""
import logging
import os

from celery import Celery
from celery.signals import beat_init

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("pauta")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@beat_init.connect
def coletar_ao_iniciar_beat(sender=None, **kwargs):
    """No primeiro start do beat (sem agenda salva), coleta logo em vez de esperar 40 min."""
    try:
        import django
        from django.apps import apps as django_apps

        if not django_apps.ready:
            django.setup()
        from apps.coleta.agendamento import disparar_se_atrasada

        disparar_se_atrasada(sender)
    except Exception:  # nunca impede o beat de subir
        logging.getLogger("apps.coleta").exception("Falha ao verificar coleta atrasada no start.")
