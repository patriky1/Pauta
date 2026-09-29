"""Tarefas do Celery. O agendamento (a cada 40 min) fica em CELERY_BEAT_SCHEDULE no settings."""
import logging

from celery import shared_task

logger = logging.getLogger("apps.coleta")


@shared_task(name="apps.coleta.tasks.coletar_noticias", ignore_result=True)
def coletar_noticias():
    """Executada pelo Celery Beat: sincroniza todas as fontes ativas."""
    from .services import sincronizar_todas

    resumo = sincronizar_todas()
    resumo.pop("detalhes", None)
    return resumo


@shared_task(name="apps.coleta.tasks.sincronizar_fonte", ignore_result=True)
def sincronizar_fonte_tarefa(fonte_id):
    """Sincroniza uma unica fonte em segundo plano."""
    from .models import FonteNoticia
    from .services import sincronizar_fonte

    fonte = FonteNoticia.objects.filter(pk=fonte_id).select_related("categoria_padrao").first()
    if fonte is None:
        logger.warning("Fonte %s nao existe mais.", fonte_id)
        return None
    return sincronizar_fonte(fonte).status
